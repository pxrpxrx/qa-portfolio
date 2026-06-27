package com.tradingtabs.cli;

import com.tradingtabs.data.FredClient;

public class TestFred {
    public static void main(String[] args) {
        FredClient fc = new FredClient();
        System.out.println("=== Testing FRED API ===");
        try {
            String raw = fc.fetchRaw("IORB");
            System.out.println("RAW IORB:");
            System.out.println(raw.substring(0, Math.min(500, raw.length())));
        } catch (Exception e) {
            System.out.println("RAW ERROR: " + e);
            e.printStackTrace();
        }
        System.out.println();
        try {
            double v = fc.fetchLatestValue("IORB");
            System.out.println("PARSED IORB = " + v);
        } catch (Exception e) {
            System.out.println("PARSE ERROR: " + e.getMessage());
        }
        System.out.println("=== Done ===");
    }
}
