package com.tradingtabs.macro;

import com.tradingtabs.data.FredClient;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.*;
import java.util.*;

public class MacroDataClient {
    private final HttpClient http;
    private final Map<String, Double> cache;

    public MacroDataClient() {
        this.http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
        this.cache = new HashMap<>();
    }

    public record PriceSnapshot(
        double spx, double ndx, double gld, double slv, double uso,
        double tlt, double hyg, double xlf, double nvda, double srln,
        double dxy, double copper, double platinum,
        double xlk, double xlu, double xly, double xlp, double vix,
        double shy, double icln, double lac, double ita, double arkx,
        double bx, double blk, double ng, double iwm,
        double dji, double cat, double xli
    ) {}

    public PriceSnapshot fetchAll() {
        return new PriceSnapshot(
            fetchYahoo("SPY"), fetchYahoo("QQQ"),
            fetchYahoo("GLD"), fetchYahoo("SLV"), fetchYahoo("USO"),
            fetchYahoo("TLT"), fetchYahoo("HYG"), fetchYahoo("XLF"),
            fetchYahoo("NVDA"), fetchYahoo("SRLN"),
            fetchDxy(), fetchYahoo("CPER"), fetchYahoo("PPLT"),
            fetchYahoo("XLK"), fetchYahoo("XLU"), fetchYahoo("XLY"),
            fetchYahoo("XLP"), fetchYahoo("^VIX"),
            fetchYahoo("SHY"), fetchYahoo("ICLN"), fetchYahoo("LAC"),
            fetchYahoo("ITA"), fetchYahoo("ARKX"),
            fetchYahoo("BX"), fetchYahoo("BLK"), fetchYahoo("NG=F"),
            fetchYahoo("IWM"),
            fetchYahoo("^DJI"), fetchYahoo("CAT"), fetchYahoo("XLI")
        );
    }

    public double fetchYahoo(String symbol) {
        String key = "yahoo_" + symbol;
        if (cache.containsKey(key) && !cache.get(key).isNaN()) return cache.get(key);
        try {
            String encSymbol = URLEncoder.encode(symbol, StandardCharsets.UTF_8);
            String url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encSymbol
                + "?range=1d&interval=1d&includePrePost=false";
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(10))
                .header("User-Agent", "Mozilla/5.0")
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int rm = body.indexOf("\"regularMarketPrice\"");
            if (rm < 0) rm = body.indexOf("\"chartPreviousClose\"");
            if (rm < 0) return Double.NaN;
            int cs = body.indexOf(':', rm) + 1;
            int ce = body.indexOf(',', cs);
            if (ce < 0) ce = body.indexOf('}', cs);
            double v = Double.parseDouble(body.substring(cs, ce).trim());
            cache.put(key, v);
            return v;
        } catch (Exception e) { return Double.NaN; }
    }

    private double fetchDxy() {
        try {
            FredClient fac = new FredClient();
            return fac.fetchLatestValue("DTWEXBGS");
        } catch (Exception e) { return Double.NaN; }
    }

    public Map<LocalDate, Double> fetchHistory(String symbol, int days) {
        Map<LocalDate, Double> hist = new TreeMap<>();
        try {
            String range = days <= 7 ? "7d" : days <= 30 ? "1mo" : days <= 90 ? "3mo" : "1y";
            String encSymbol = URLEncoder.encode(symbol, StandardCharsets.UTF_8);
            String url = "https://query1.finance.yahoo.com/v8/finance/chart/" + encSymbol
                + "?range=" + range + "&interval=1d";
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(10))
                .header("User-Agent", "Mozilla/5.0")
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            String tsPart = extractJsonArray(body, "timestamp");
            String clPart = extractJsonArray(body, "close");
            if (tsPart == null || clPart == null) return hist;
            List<Long> timestamps = parseJsonNumbers(tsPart).stream().map(Double::longValue).toList();
            List<Double> closes = parseJsonNumbers(clPart);
            for (int i = 0; i < timestamps.size() && i < closes.size(); i++) {
                if (!closes.get(i).isNaN())
                    hist.put(LocalDate.ofEpochDay(timestamps.get(i) / 86400), closes.get(i));
            }
        } catch (Exception ignored) {}
        return hist;
    }

    private String extractJsonArray(String json, String key) {
        int idx = json.indexOf("\"" + key + "\"");
        if (idx < 0) return null;
        int start = json.indexOf('[', idx);
        if (start < 0) return null;
        int depth = 0;
        for (int i = start; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '[') depth++;
            else if (c == ']') { depth--; if (depth == 0) return json.substring(start, i + 1); }
        }
        return null;
    }

    private List<Double> parseJsonNumbers(String array) {
        List<Double> nums = new ArrayList<>();
        String inner = array.substring(1, array.length() - 1);
        if (inner.isBlank()) return nums;
        for (String s : inner.split(",")) {
            s = s.trim();
            try { nums.add(s.equals("null") ? Double.NaN : Double.parseDouble(s)); }
            catch (Exception e) { nums.add(Double.NaN); }
        }
        return nums;
    }
}
