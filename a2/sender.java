import java.io.FileInputStream;
import java.io.FileWriter;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.ArrayList; 
import java.util.Timer;
import java.util.TimerTask;

class ack_receiver extends Thread {
  public void run() {
    try {
      // Create socket to listen for ACKs from emulator at receive_port
      DatagramSocket ds = new DatagramSocket(sender.receive_port);
      // Create DatagramPacket for receiving ack
      byte[] receive = new byte[512]; 
      DatagramPacket receiveAck = new DatagramPacket(receive, receive.length);
      while (true) {
        ds.receive(receiveAck);
        // parse buffer into packet
        packet p = packet.parseUDPdata(receive);
        int seqNum = p.getSeqNum();
        // Exit the server if EOT received
        if (p.getType() == 2) {
          sender.seqnum_log.close();
          sender.ack_log.close();
          System.exit(0);
        }
        // log ack sequence numbers in ack.log
        sender.ack_log.write(seqNum + "\n");
        // if seqNum overflows, adjust sender base accordingly
        sender.base = 32*((sender.nextSeqNum-seqNum)/32) + (seqNum+1)%32;
        // Send EOT if all acks received
        if (seqNum == (sender.packets.size()-1)%32 && sender.nextSeqNum == sender.packets.size()) {
          packet eot = packet.createEOT(seqNum+1);
          sender.udt_send(eot);
        }
        // stop timer if window empty
        if (sender.base == sender.nextSeqNum) {
          sender.timer.cancel();
          sender.timer.purge();
        } else {
          sender.timer.schedule(new sender.Timeout(), 100);
        }
      }
    } catch (Exception e) {
      System.out.println(e);
    }
  }
}

public class sender {
  public static int base = 0;
  public static int nextSeqNum = 0;
  static final int N = 10;
  static final Timer timer = new Timer();
  static ArrayList<packet> packets = new ArrayList<packet>();
  static String host_address;
  static int emulator_port;
  public static int receive_port;
  static String file_name;
  static FileWriter seqnum_log;
  static FileWriter ack_log;

  static class Timeout extends TimerTask {
    public void run() {
      System.out.println("Time's up");
      // Schedule new timer
      timer.schedule(new Timeout(), 100);
      // Retransmit packets
      for (int i = base; i < nextSeqNum; i++) {
        udt_send(packets.get(i));
      }
    }
  }

  public static void udt_send(packet p) {
    byte[] sendBuffer = new byte[512];
    sendBuffer = p.getUDPdata();
    try { 
      // log sequence numbers in seqnum.log
      if (p.getType() != 2) seqnum_log.write(p.getSeqNum() + "\n");

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
      System.out.println("Proper usage: <emulator hostname> <emulator receiving UDP port from sender> <sender UDP port> <input file>");
      System.exit(0);
    }
    // Parse command line arguments
    host_address = args[0];
    emulator_port = Integer.parseInt(args[1]);
    receive_port = Integer.parseInt(args[2]);
    file_name = args[3];
    // Start thread to receive acks from emulator
    ack_receiver ar = new ack_receiver();
    ar.start();
    try {
      // Read file into packets
      FileInputStream fis = new FileInputStream(file_name);
      byte[] readBuffer = new byte[500];
      int i = 0, len;
      while ((len = fis.read(readBuffer)) > 0) {
        packet p = packet.createPacket(i, new String(readBuffer, 0, len));
        packets.add(p);
        i++;
      }
      fis.close();
      System.out.println("N: " + N);
      System.out.println("Total packets: " + packets.size());
      // initiate FileWriter objects
      seqnum_log = new FileWriter("seqnum.log");
      ack_log = new FileWriter("ack.log");

      int timeSlice = 0;
      while (true) {
        timeSlice++;
        if (timeSlice % 1000 == 0) System.out.print(".");
        // stop sending if all packets have been sent
        if (nextSeqNum == packets.size()) break;
        if (nextSeqNum < base + N) {
          udt_send(packets.get(nextSeqNum));
          if (base == nextSeqNum) {
            // start timer
            timer.schedule(new Timeout(), 100);
          }
          nextSeqNum++;
        }
      }
    } catch (Exception e) {
      System.err.println("Error: " + e);
    }
  }
}
