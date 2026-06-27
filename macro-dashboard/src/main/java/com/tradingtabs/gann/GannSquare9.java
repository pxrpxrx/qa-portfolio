package com.tradingtabs.gann;

import java.util.*;

public class GannSquare9 {

    public record Level(double price, double angle, String cross) {
        public String label() {
            return String.format("$%,.0f @ %.0f° (%s)", price, angle, cross);
        }
    }

    public static double priceToAngle(double price) {
        if (price <= 0) return 0;
        double sqrt = Math.sqrt(price);
        double deg = (sqrt * 180) - 225;
        deg = deg % 360;
        return deg < 0 ? deg + 360 : deg;
    }

    public static double angleToPrice(double angle, int ring) {
        double rad = Math.toRadians(angle);
        double sqrt = (rad / Math.PI + 1.25) + 2 * ring;
        double p = sqrt * sqrt;
        return p > 0 ? p : Double.NaN;
    }

    private static final double[] KEY_ANGLES = {0, 45, 90, 135, 180, 225, 270, 315};
    private static final double CARDINAL_START = 0;
    private static final double FIXED_START = 45;

    public static List<Level> getSupportResistance(double price, int levelsAbove, int levelsBelow) {
        Set<Long> seen = new HashSet<>();
        List<Level> result = new ArrayList<>();
        double sqrt0 = Math.sqrt(price);
        double deg = priceToAngle(price);

        for (double target : KEY_ANGLES) {
            double delta = (target - deg) / 360;
            int nAbove = (int) Math.ceil(delta);
            int nBelow = (int) Math.floor(delta);

            for (int i = nBelow - levelsBelow + 1; i < nBelow; i++) {
                double p = (sqrt0 + i * 2) * (sqrt0 + i * 2);
                if (p > 0 && seen.add(Math.round(p))) result.add(new Level(p, target, target % 90 == 0 ? "CARDINAL" : "FIXED"));
            }
            for (int i = nAbove; i < nAbove + levelsAbove; i++) {
                double p = (sqrt0 + i * 2) * (sqrt0 + i * 2);
                if (p > 0 && seen.add(Math.round(p))) result.add(new Level(p, target, target % 90 == 0 ? "CARDINAL" : "FIXED"));
            }
        }

        result.sort(Comparator.comparingDouble(Level::price));
        return result;
    }

    public static List<String> formatBlock(double price) {
        List<String> lines = new ArrayList<>();
        double angle = priceToAngle(price);
        double sqrt = Math.sqrt(price);
        int ring = (int)((sqrt + 1) / 2);
        if (ring < 1) ring = 1;

        lines.add(String.format("  Price: $%,.0f | Ring: %d | Angle: %.1f°", price, ring, angle));

        // Determine which cross
        String cross;
        int nearest = (int)Math.round(angle / 45) * 45;
        if (nearest % 90 == 0) cross = "CARDINAL CROSS";
        else cross = "FIXED CROSS";
        lines.add(String.format("  Cross: %s (nearest %.0f°)", cross, (double)nearest));

        // Key levels
        lines.add("  Key levels:");
        List<Level> levels = getSupportResistance(price, 3, 3);
        int count = 0;
        for (Level l : levels) {
            if (count >= 6) break;
            String marker = l.price() > price ? "  R" : l.price() < price ? "  S" : "  *";
            double pct = (l.price() - price) / price * 100;
            lines.add(String.format("    %s $%,.0f (%.1f%%)", marker, l.price(), pct));
            count++;
        }

        // Squared price levels (ring multiples)
        lines.add("  Squared prices:");
        for (int r = Math.max(1, ring - 2); r <= ring + 2; r++) {
            double sp = (2 * r - 1) * (2 * r - 1);
            String m = Math.abs(sp - price) / price < 0.02 ? " <--" : "";
            lines.add(String.format("    (2n-1)² n=%d → $%,.0f%s", r, sp, m));
        }

        return lines;
    }

    public static String shortSummary(double price) {
        double angle = priceToAngle(price);
        int nearest = (int)Math.round(angle / 45) * 45;
        String cross = nearest % 90 == 0 ? "CARDINAL" : "FIXED";
        double sqrt = Math.sqrt(price);
        int ring = (int)((sqrt + 1) / 2);
        return String.format("$%,.0f → Ring %d, %.0f° %s", price, ring, (double)nearest, cross);
    }
}
