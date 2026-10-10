package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"

	"github.com/joho/godotenv"
)

const (
	protocolICMP = 1
	timeout      = 10 * time.Second
	channelSize  = 16
	reaperPeriod = 5 * time.Second
)

// pingData is the complete record passed to the capture routine. This is the
// type that can later be written to a database instead of (or in addition to)
// the console.
// type pingData struct {
// 	id         int
// 	target     net.IP
// 	source     net.Addr
// 	sequence   int
// 	sentAt     time.Time
// 	receivedAt time.Time
// 	rtt        time.Duration
// 	err        error
// }

type pingTrackerKey struct {
	workerId int
	sequence uint16
}

func main() {
	fmt.Println("Startup")

	err := godotenv.Load()
	if err != nil {
		log.Printf("No .env file found, using environment variables")
	}

	settings := NewSettings()
	writerContext, cancelWriter := context.WithTimeout(context.Background(), 10*time.Second)
	measurementWriter, err := NewQuestDBWriter(writerContext, settings.qwestDBAddress)
	cancelWriter()
	if err != nil {
		log.Fatalf("Unable to initialize QuestDB writer: %v", err)
	}

	backendClient := NewBackendClient("http://" + settings.apiBindHost + ":" + settings.apiBindPort)
	destinations, err := backendClient.GetPingDestinations()
	if err != nil {
		log.Fatal(err)
	}

	conn, err := icmp.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		log.Fatalf("Unable to open ICMP socket: %v", err)
	}
	defer func() {
		err := conn.Close()
		if err != nil {
			log.Fatalf("Unable to close ICMP socket: %v", err)
		}
	}()

	mainctx, cancelMain := context.WithCancel(context.Background())
	manager := NewWorkerManager()
	pingStats := NewPingStats()

	replies := make(chan PingData, channelSize)
	receiveErrors := make(chan PingData, channelSize)
	receiveTimeout := make(chan PingData, channelSize)

	workerBaseID := os.Getpid() & 0xffff
	packetTracker := NewSafeMap[pingTrackerKey, PingData]()

	ctx, cancel := context.WithCancel(context.Background())
	go receivePings(ctx, conn, packetTracker, pingStats, replies, receiveErrors)
	go reaperScan(ctx, packetTracker, pingStats, receiveTimeout)
	go processPings(ctx, packetTracker, pingStats, replies, receiveErrors, receiveTimeout, measurementWriter)

	startConfiguredPingers(destinations, workerBaseID, manager, conn, packetTracker, pingStats, receiveErrors)

	controlServer := NewControlServer(cancelMain, manager, pingStats, settings.pingControlServerListenAddress)
	go func() {
		if err := controlServer.Start(); err != nil {
			log.Fatal(err)
		}
	}()

	for {
		select {
		case <-mainctx.Done():
			fmt.Println("Shutting down")
			manager.StopAll()
			cancel()
			time.Sleep(2 * time.Second)
			performReaping(packetTracker, pingStats, receiveErrors)
			packetTracker.Range(func(key pingTrackerKey, data PingData) bool {
				fmt.Printf("%+v: %+v\n", key, data)
				return true
			})
			fmt.Printf("%+v\n", pingStats)
			return
		}
	}
}

func startConfiguredPingers(destinations []PingDestination, workerBaseID int, manager *WorkerManager, conn *icmp.PacketConn, packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, receiveErrors chan PingData) {
	for index, pingDestination := range destinations {
		if !pingDestination.Enabled {
			fmt.Printf("Skipping disabled destination %s\n", pingDestination.Name)
			continue
		}

		switch pingDestination.AddressType {
		case "IPV4":
			ip, err := resolveIPv4(pingDestination.IPv4)
			if err != nil {
				log.Printf("Unable to resolve %s: %v", pingDestination.IPv4, err)
				continue
			}
			startIPV4Pinger(ip, pingDestination, workerBaseID, index, manager, conn, packetTracker, pingStats, receiveErrors)
		case "IPV6":
		case "HOST":
			ips, err := net.LookupIP(pingDestination.Host)
			if err != nil {
				log.Printf("Unable to resolve %s: %v", pingDestination.Host, err)
				continue
			}
			for _, dnsIP := range ips {
				fmt.Printf("Resolved %s to %s\n", pingDestination.Host, dnsIP)
				ip, resolveErr := resolveIPv4(dnsIP.String())
				if resolveErr != nil {
					continue
				}
				startIPV4Pinger(ip, pingDestination, workerBaseID, index, manager, conn, packetTracker, pingStats, receiveErrors)
				break
			}
		}
	}
}

func startIPV4Pinger(ip *net.IPAddr, pingDestination PingDestination, workerBaseID int, index int, manager *WorkerManager, conn *icmp.PacketConn, packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, receiveErrors chan PingData) {
	fmt.Printf("PingArchive-engine monitoring %s (%s)\n", pingDestination.Name, ip)
	workerID := workerBaseID + index
	if errStart := manager.Start(workerID, func(ctx context.Context, worker *Worker) {
		if errStartPinger := startPinger(ctx, worker, conn, ip, pingDestination, workerID, packetTracker, pingStats, receiveErrors, pingDestination.PingInterval); errStartPinger != nil {
			fmt.Println(errStartPinger)
		}
	}); errStart != nil {
		fmt.Println(errStart)
	}
}

// startPinger
// - starts the ping loop
// - sends a ping
func startPinger(ctx context.Context, worker *Worker, conn *icmp.PacketConn, ip *net.IPAddr, pingDestination PingDestination, id int, packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, receiveErrors chan<- PingData, interval int) error {
	ticker := time.NewTicker(time.Duration(interval) * time.Second)
	defer ticker.Stop()
	sequenceNumber := uint16(1)
	for {
		select {
		case <-ctx.Done():
			fmt.Println(id, ": stopping")
			return fmt.Errorf("stopped worker id: %d", id)
		case <-ticker.C:
			sentAt := time.Now()
			worker.SetLastRunAt(sentAt)
			newPingData := PingData{
				id:              id,
				destinationID:   pingDestination.ID,
				destinationName: pingDestination.Name,
				target:          ip.IP,
				sequence:        sequenceNumber,
				sentAt:          sentAt,
				err:             nil,
			}

			trackerKey := pingTrackerKey{workerId: id, sequence: sequenceNumber}
			packetTracker.Set(trackerKey, newPingData)
			if err := sendPing(conn, ip, id, sequenceNumber); err != nil {
				pingStats.IncrementFailure()
				newPingData.err = err
				packetTracker.Remove(trackerKey)
				receiveErrors <- newPingData
			}
			sequenceNumber++
		}
	}
}

func resolveIPv4(host string) (*net.IPAddr, error) {
	ips, err := net.LookupIP(host)
	if err != nil {
		return nil, err
	}

	for _, ip := range ips {
		if ipv4 := ip.To4(); ipv4 != nil {
			return &net.IPAddr{IP: ipv4}, nil
		}
	}

	return nil, fmt.Errorf("no IPv4 address found for %s", host)
}

func sendPing(
	conn *icmp.PacketConn,
	target *net.IPAddr,
	id int,
	seq uint16,
) error {

	message := icmp.Message{
		Type: ipv4.ICMPTypeEcho,
		Code: 0,
		Body: &icmp.Echo{
			ID:   id,
			Seq:  int(seq),
			Data: []byte("PingArchive"),
		},
	}

	data, err := message.Marshal(nil)
	if err != nil {
		return err
	}

	destination := &net.IPAddr{
		IP: target.IP,
	}

	if _, err := conn.WriteTo(data, destination); err != nil {
		return err
	}

	return nil
}

func receivePings(
	ctx context.Context,
	conn *icmp.PacketConn,
	packetTracker *SafeMap[pingTrackerKey, PingData],
	pingStats *PingStats,
	replies chan<- PingData,
	receiveErrors chan<- PingData,
) {
	buffer := make([]byte, 1500)

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Receiver stopping")
			return
		default:
			conn.SetReadDeadline(time.Now().Add(500 * time.Millisecond))
			n, peer, err := conn.ReadFrom(buffer)
			if err != nil {
				if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
					continue
				}
				// errors <- err
				return
			}

			receivedAt := time.Now()
			reply, err := icmp.ParseMessage(protocolICMP, buffer[:n])
			if err != nil {
				continue
			}

			if reply.Type != ipv4.ICMPTypeEchoReply {
				continue
			}
			echo, ok := reply.Body.(*icmp.Echo)
			if !ok {
				continue
			}

			pkey := pingTrackerKey{
				workerId: echo.ID,
				sequence: uint16(echo.Seq),
			}

			data, ok := packetTracker.Get(pkey)
			if !ok {
				pingStats.IncrementSkipped()
			} else {
				data.UpdateReceivedAt(receivedAt)
				data.source = peer
				packetTracker.Set(pkey, data)
				pingStats.IncrementSuccess()
				replies <- data
				packetTracker.Remove(pkey)
			}
		}
	}
}

func capturePing(data PingData) {
	if data.err != nil {
		fmt.Printf("%s seq=%d sent=%s timeout/error: %v\n",
			data.target,
			data.sequence,
			data.sentAt.Format(time.RFC3339Nano),
			data.err,
		)
		return
	}

	fmt.Printf("%s seq=%d source=%s sent=%s received=%s time=%v\n",
		data.target,
		data.sequence,
		data.source,
		data.sentAt.Format(time.RFC3339Nano),
		data.receivedAt.Format(time.RFC3339Nano),
		data.rtt.Round(time.Microsecond),
	)
}

func reaperScan(
	ctx context.Context,
	packetTracker *SafeMap[pingTrackerKey, PingData],
	pingStats *PingStats,
	receiveErrors chan<- PingData,

) {
	ticker := time.NewTicker(reaperPeriod)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			fmt.Println("Reaper stopping")
			return
		case <-ticker.C:
			performReaping(packetTracker, pingStats, receiveErrors)
		}
	}
}

func performReaping(packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, receiveTimeout chan<- PingData) {
	var expired []pingTrackerKey
	packetTracker.Range(func(key pingTrackerKey, value PingData) bool {
		if time.Since(value.sentAt) > reaperPeriod {
			expired = append(expired, key)
		}
		return true
	})
	for _, key := range expired {
		data, ok := packetTracker.Get(key)
		if ok {
			packetTracker.Remove(key)
			pingStats.IncrementTimeout()
			receiveTimeout <- data
		}
	}
}

func processPings(ctx context.Context, packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, replies <-chan PingData, receiveErrors <-chan PingData, receiveTimeout <-chan PingData, writer PingMeasurementWriter) {
	writeMeasurement := func(data PingData, outcome string) {
		capturePing(data)
		if err := writer.WritePing(ctx, data, outcome); err != nil {
			log.Printf("Unable to write %s ping measurement for destination %d: %v", outcome, data.destinationID, err)
		}
	}

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Process Pings stopping")
			closeContext, cancelClose := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancelClose()
			if err := writer.Close(closeContext); err != nil {
				log.Printf("Unable to close QuestDB writer: %v", err)
			}
			return
		case data := <-replies:
			writeMeasurement(data, "reply")
		case data := <-receiveErrors:
			writeMeasurement(data, "send_error")
		case data := <-receiveTimeout:
			writeMeasurement(data, "timeout")
		}
	}
}
