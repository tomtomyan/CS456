import java.io.FileWriter;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class receiver {
  public static String host_address;
  public static int emulator_port;
  public static int receive_port;
  public static String file_name;

  public static void udt_send(packet p) {
    byte[] sendBuffer = new byte[512];
    sendBuffer = p.getUDPdata();
    try { 
      DatagramSocket ds = new DatagramSocket();
      DatagramPacket dp = new DatagramPacket(sendBuffer, 512, InetAddress.getByName(host_address), emulator_port);
      ds.send(dp);
    } catch (Exception e) {
      System.err.println("Error: " + e);
    }
  }

  public static void main(String[] args) {
    if (args.length != 4) {
      System.out.println("Incorrect number of command line arguments");
      System.out.println("Proper usage: <emulator hostname> <emulator receiving UDP port> <receiver UDP port> <output file>");
      System.exit(0);
    }
    // Parse command line arguments
    host_address = args[0];
    emulator_port = Integer.parseInt(args[1]);
    receive_port = Integer.parseInt(args[2]);
    file_name = args[3];

    int expectedSeqNum = 0;
    try {
      // Create a socket to listen on the port
      DatagramSocket ds = new DatagramSocket(receive_port);
      // Create packet length buffer to read datagrams
      byte[] buffer = new byte[512];
      // Create packet to put data into buffer
      DatagramPacket receivePacket = new DatagramPacket(buffer, buffer.length);
      // Create FileWriter objects
      FileWriter fw = new FileWriter(file_name);
      FileWriter log = new FileWriter("arrival.log");
      // Loop until EOT
      while (true) {
        ds.receive(receivePacket);
        // parse buffer into packet
        packet p = packet.parseUDPdata(buffer);
        int seqNum = p.getSeqNum();
        int type = p.getType();

        if (type == 2) { // EOT packet
          packet eot = packet.createEOT(seqNum);
          udt_send(eot);
          // exit receiver
          fw.close();
          log.close();
          System.exit(0);
        }
        // log sequence numbers in arrival.log
        log.write(seqNum + "\n");
        System.out.println(seqNum);

        if (seqNum == expectedSeqNum) {
          // extract data and deliver to output file
          fw.write(p.getString());
          // send ack
          packet ack = packet.createACK(seqNum);
          udt_send(ack);
          if (expectedSeqNum == 31) {
            expectedSeqNum = 0;
            continue;
          }
          expectedSeqNum++;
        } else if (expectedSeqNum != 0) { // if we receive an out of order packet that's not the first
          packet ack = packet.createACK(expectedSeqNum-1);
          udt_send(ack);
        }
      }
    } catch (Exception e) {
      System.err.println(e);
    }
  }
}
