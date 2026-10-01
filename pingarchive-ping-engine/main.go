package main

import (
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
	timeout      = 2 * time.Second
)

// pingReply is produced by the receiver goroutine after it validates an ICMP
// echo reply. Keeping socket reads in one place also makes it safe to add more
// ping targets later.
type pingReply struct {
	sequence   int
	receivedAt time.Time
	peer       net.Addr
}

// pingData is the complete record passed to the capture routine. This is the
// type that can later be written to a database instead of (or in addition to)
// the console.
type pingData struct {
	target     net.IP
	source     net.Addr
	sequence   int
	sentAt     time.Time
	receivedAt time.Time
	rtt        time.Duration
	err        error
}

func main() {
	fmt.Println("Startup")

	host := "8.8.8.8"
	ip, err := resolveIPv4(host)

	if err != nil {
		log.Fatalf("Unable to resolve %s: %v", host, err)
	}

	fmt.Printf("PingArchive monitoring %s (%s)\n", host, ip)

	conn, err := icmp.ListenPacket("udp4", "0.0.0.0")
	if err != nil {
		log.Fatalf("Unable to open ICMP socket: %v", err)
	}
	defer conn.Close()

	id := os.Getpid() & 0xffff

	replies := make(chan pingReply, 16)
	receiveErrors := make(chan error, 1)
	go receivePings(conn, id, replies, receiveErrors)

	for seq := 1; ; seq++ {
		sentAt := time.Now()
		if err := sendPing(conn, ip, id, seq); err != nil {
			capturePing(pingData{
				target:   ip.IP,
				sequence: seq,
				sentAt:   sentAt,
				err:      err,
			})
		} else {
			capturePing(awaitReply(ip.IP, seq, sentAt, replies, receiveErrors))
		}

		time.Sleep(time.Second)
	}
}

// startPinger
// - starts the ping loop
// - sends a ping
func startPinger(conn *icmp.PacketConn, ip *net.IPAddr, id int) int {
	for seq := 1; ; seq++ {
		sentAt := time.Now()
		if err := sendPing(conn, ip, id, seq); err != nil {
			capturePing(pingData{
				target:   ip.IP,
				sequence: seq,
				sentAt:   sentAt,
				err:      err,
			})
		}
		time.Sleep(time.Second)
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
	conn *icmp.PacketConn,
	id int,
	replies chan<- pingReply,
	errors chan<- error,
) {
	buffer := make([]byte, 1500)

	for {
		n, peer, err := conn.ReadFrom(buffer)
		if err != nil {
			errors <- err
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
		if !ok || echo.ID != id {
			continue
		}

		replies <- pingReply{
			sequence:   echo.Seq,
			receivedAt: receivedAt,
			peer:       peer,
		}
	}
}

func awaitReply(
	target net.IP,
	sequence int,
	sentAt time.Time,
	replies <-chan pingReply,
	receiveErrors <-chan error,
) pingData {
	timer := time.NewTimer(timeout)
	defer timer.Stop()

	for {
		select {
		case reply := <-replies:
			// A reply can arrive after its caller has timed out. Ignore that stale
			// reply and keep waiting for the sequence currently being measured.
			if reply.sequence != sequence {
				continue
			}

			return pingData{
				target:     target,
				source:     reply.peer,
				sequence:   sequence,
				sentAt:     sentAt,
				receivedAt: reply.receivedAt,
				rtt:        reply.receivedAt.Sub(sentAt),
			}
		case err := <-receiveErrors:
			return pingData{
				target:   target,
				sequence: sequence,
				sentAt:   sentAt,
				err:      fmt.Errorf("receiver stopped: %w", err),
			}
		case <-timer.C:
			return pingData{
				target:   target,
				sequence: sequence,
				sentAt:   sentAt,
				err:      fmt.Errorf("timeout after %v", timeout),
			}
		}
	}
}

// capturePing is the single output path for ping measurements. Replace or
// extend this function when the database writer is added.
func capturePing(data pingData) {
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
