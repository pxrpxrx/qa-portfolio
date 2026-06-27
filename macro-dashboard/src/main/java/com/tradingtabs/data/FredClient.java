package com.tradingtabs.data;

import java.net.URI;
import java.net.http.*;
import java.time.*;
import java.util.*;

public class FredClient {
    private static final String BASE = "https://api.stlouisfed.org/fred/series/observations";
    private static final String KEY = "031f70552bb618fc2672f533f3138e8d";
    private final HttpClient http;

    public FredClient() {
        this.http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    }

    public record Observation(LocalDate date, double value) {}

    public List<Observation> fetchSeries(String seriesId, LocalDate from, LocalDate to) {
        String url = BASE + "?series_id=" + seriesId
            + "&api_key=" + KEY
            + "&file_type=json"
            + "&observation_start=" + from
            + "&observation_end=" + to
            + "&sort_order=asc";
        String body = get(url);
        return parseObservations(body);
    }

    public Observation fetchLatest(String seriesId) {
        String url = BASE + "?series_id=" + seriesId
            + "&api_key=" + KEY
            + "&file_type=json"
            + "&sort_order=desc&limit=1";
        String body = get(url);
        List<Observation> list = parseObservations(body);
        return list.isEmpty() ? null : list.get(0);
    }

    public double fetchLatestValue(String seriesId) {
        try {
            Observation obs = fetchLatest(seriesId);
            return obs != null ? obs.value() : Double.NaN;
        } catch (Exception e) { return Double.NaN; }
    }

    private String get(String url) {
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(15))
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            return resp.body();
        } catch (Exception e) {
            System.err.println("[FredClient] WARN: " + e.getClass().getSimpleName() + " for " + url.substring(0, Math.min(80, url.length())));
            throw new RuntimeException("FRED API error", e);
        }
    }

    public String fetchRaw(String seriesId) {
        String url = BASE + "?series_id=" + seriesId
            + "&api_key=" + KEY
            + "&file_type=json"
            + "&sort_order=desc&limit=2";
        return get(url);
    }

    private List<Observation> parseObservations(String json) {
        List<Observation> result = new ArrayList<>();
        try {
            String obsArray = extractArray(json, "\"observations\"");
            if (obsArray == null) return result;
            List<String> items = splitObjects(obsArray);
            for (String item : items) {
                String dateStr = extractString(item, "\"date\"");
                String valStr = extractString(item, "\"value\"");
                if (dateStr == null || valStr == null || valStr.equals(".")) continue;
                LocalDate d = LocalDate.parse(dateStr);
                double v = Double.parseDouble(valStr);
                result.add(new Observation(d, v));
            }
        } catch (Exception ignored) {}
        return result;
    }

    public static String extractArray(String json, String key) {
        int idx = json.indexOf(key);
        if (idx < 0) return null;
        int arrStart = json.indexOf('[', idx);
        if (arrStart < 0) return null;
        int depth = 0;
        for (int i = arrStart; i < json.length(); i++) {
            char c = json.charAt(i);
            if (c == '[') depth++;
            else if (c == ']') { depth--; if (depth == 0) return json.substring(arrStart, i + 1); }
        }
        return null;
    }

    public static List<String> splitObjects(String array) {
        List<String> items = new ArrayList<>();
        int i = 0;
        while (i < array.length()) {
            int start = array.indexOf('{', i);
            if (start < 0) break;
            int depth = 0;
            for (int j = start; j < array.length(); j++) {
                char c = array.charAt(j);
                if (c == '{') depth++;
                else if (c == '}') { depth--; if (depth == 0) { items.add(array.substring(start, j + 1)); i = j + 1; break; } }
            }
        }
        return items;
    }

    public static String extractString(String json, String key) {
        int idx = json.indexOf(key);
        if (idx < 0) return null;
        int colon = json.indexOf(':', idx + key.length());
        if (colon < 0) return null;
        int valStart = json.indexOf('"', colon);
        if (valStart < 0) return null;
        int valEnd = json.indexOf('"', valStart + 1);
        if (valEnd < 0) return null;
        return json.substring(valStart + 1, valEnd);
    }
}
