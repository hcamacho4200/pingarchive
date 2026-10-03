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
	sequence int
}

func main() {
	fmt.Println("Startup")

	conn, err := icmp.ListenPacket("udp4", "0.0.0.0")
	if err != nil {
		log.Fatalf("Unable to open ICMP socket: %v", err)
	}
	defer func() {
		err := conn.Close()
		if err != nil {
			log.Fatalf("Unable to close ICMP socket: %v", err)
		}
	}()

	manager := NewWorkerManager()
	pingStats := NewPingStats()
	controlServer := NewControlServer(manager, pingStats, "0.0.0.0:8100")
	go func() {
		if err := controlServer.Start(); err != nil {
			log.Fatal(err)
		}
	}() 

	// replies := make(chan pingReply, 16)
	receiveErrors := make(chan PingData, channelSize)

	workerBaseID := os.Getpid() & 0xffff
	packetTracker := NewSafeMap[pingTrackerKey, PingData]()


	ctx, cancel := context.WithCancel(context.Background())
	go receivePings(ctx, conn, packetTracker, pingStats)
	go reaperScan(ctx, packetTracker, pingStats)

	hosts := []string{
		"8.8.8.8",
		"1.1.1.1",
	}

	for index, hostAddress := range hosts {
		ip, err := resolveIPv4(hostAddress)
		if err != nil {
			log.Fatalf("Unable to resolve %s: %v", hostAddress, err)
		}

		fmt.Printf("PingArchive-engine monitoring %s (%s)\n", hostAddress, ip)
		workerID := workerBaseID + index
		if errStart := manager.Start(workerID, func(ctx context.Context) {
			if errStartPinger := startPinger(conn, ip, workerID, packetTracker, pingStats, receiveErrors, ctx); errStartPinger != nil {
				fmt.Println(errStartPinger)
			}
		}); errStart != nil {
			fmt.Println(errStart)
		}
	}

	time.Sleep(5 * time.Second)
	if err := manager.Stop(workerBaseID + 1); err != nil {
		fmt.Println(err)
	}
	time.Sleep(5 * time.Second)
	manager.StopAll()
	fmt.Println("Shutting down")
	time.Sleep(2 * time.Second)
	cancel()
	performReaping(packetTracker, pingStats)
	packetTracker.Range(func(key pingTrackerKey, data PingData) bool {
		fmt.Printf("%+v: %+v\n", key, data)
		return true

	})
	fmt.Printf("%+v\n", pingStats)
}

// startPinger
// - starts the ping loop
// - sends a ping
func startPinger(conn *icmp.PacketConn, ip *net.IPAddr, id int, packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats, receiveErrors chan<- PingData, ctx context.Context) error {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()
	sequenceNumber := 1
	for {
		select {
		case <-ctx.Done():
			fmt.Println(id, ": stopping")
			return fmt.Errorf("stopped worker id: %d", id)
		case <-ticker.C:
			sentAt := time.Now()
			newPingData := PingData{
				id:       id,
				target:   ip.IP,
				sequence: sequenceNumber,
				sentAt:   sentAt,
				err:      nil,
			}

			fmt.Println(id, ": ping ", sentAt.Format(time.RFC3339Nano))
			packetTracker.Set(pingTrackerKey{workerId: id, sequence: sequenceNumber}, newPingData)
			if err := sendPing(conn, ip, id, sequenceNumber); err != nil {
				pingStats.IncrementFailure()
				newPingData.err = err
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
	seq int,
) error {

	message := icmp.Message{
		Type: ipv4.ICMPTypeEcho,
		Code: 0,
		Body: &icmp.Echo{
			ID:   id,
			Seq:  seq,
			Data: []byte("PingArchive"),
		},
	}

	data, err := message.Marshal(nil)
	if err != nil {
		return err
	}

	destination := &net.UDPAddr{
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
				sequence: echo.Seq,
			}

			data, ok := packetTracker.Get(pkey)
			if !ok {
				fmt.Printf("skipping: %+v\n", data)
				pingStats.IncrementSkipped()
			} else {
				data.UpdateReceivedAt(receivedAt)
				data.target = peer.(*net.UDPAddr).IP
				packetTracker.Set(pkey, data)
				pingStats.IncrementSuccess()
				fmt.Printf("reply: %+v\n", data)
			}

			// echo, ok := reply.Body.(*icmp.Echo)
			// if !ok || echo.ID != id {
			// 	continue
			// }

			// 		replies <- pingReply{
			// 			sequence:   echo.Seq,
			// 			receivedAt: receivedAt,
			// 			peer:       peer,
			// 		}
		}
	}
}

// func awaitReply(
// 	target net.IP,
// 	sequence int,
// 	sentAt time.Time,
// 	replies <-chan pingReply,
// 	receiveErrors <-chan error,
// ) pingData {
// 	timer := time.NewTimer(timeout)
// 	defer timer.Stop()

// 	for {
// 		select {
// 		case reply := <-replies:
// 			// A reply can arrive after its caller has timed out. Ignore that stale
// 			// reply and keep waiting for the sequence currently being measured.
// 			if reply.sequence != sequence {
// 				continue
// 			}

// 			return pingData{
// 				target:     target,
// 				source:     reply.peer,
// 				sequence:   sequence,
// 				sentAt:     sentAt,
// 				receivedAt: reply.receivedAt,
// 				rtt:        reply.receivedAt.Sub(sentAt),
// 			}
// 		case err := <-receiveErrors:
// 			return pingData{
// 				target:   target,
// 				sequence: sequence,
// 				sentAt:   sentAt,
// 				err:      fmt.Errorf("receiver stopped: %w", err),
// 			}
// 		case <-timer.C:
// 			return pingData{
// 				target:   target,
// 				sequence: sequence,
// 				sentAt:   sentAt,
// 				err:      fmt.Errorf("timeout after %v", timeout),
// 			}
// 		}
// 	}
// }

// capturePing is the single output path for ping measurements. Replace or
// extend this function when the database writer is added.
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

) {
	ticker := time.NewTicker(reaperPeriod)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			fmt.Println("Reaper stopping")
			return
		case <-ticker.C:
			performReaping(packetTracker, pingStats)
		}
	}
}

func performReaping(packetTracker *SafeMap[pingTrackerKey, PingData], pingStats *PingStats) {
	fmt.Println("reaping")
	var expired []pingTrackerKey
	packetTracker.Range(func(key pingTrackerKey, value PingData) bool {
		if time.Since(value.sentAt) > reaperPeriod {
			expired = append(expired, key)
		}
		return true
	})
	for _, key := range expired {
		packetTracker.Remove(key)
		pingStats.IncrementTimeout()
	}
}
