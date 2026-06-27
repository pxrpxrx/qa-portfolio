package com.tradingtabs.data;

import java.net.URI;
import java.net.http.*;
import java.time.*;
import java.util.*;

public class CryptoClient {
    private final HttpClient http;

    public CryptoClient() { this.http = HttpClient.newHttpClient(); }

    public record Ticker(double price, double volume24h, double oi, double fundingRate) {}

    public Ticker fetchBtcTicker() {
        try {
            double price = fetchBinancePrice();
            double funding = fetchBinanceFunding();
            double oi = fetchBinanceOi();
            double volume = fetchCoinGeckoVolume();
            return new Ticker(price, volume, oi, funding);
        } catch (Exception e) { return new Ticker(Double.NaN, Double.NaN, Double.NaN, Double.NaN); }
    }

    public double fetchBtcPrice() {
        try {
            HttpRequest req = HttpRequest.newBuilder(
                URI.create("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"))
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int idx = body.indexOf("\"price\"");
            if (idx < 0) return Double.NaN;
            int cs = body.indexOf('"', idx + 8) + 1;
            int ce = body.indexOf('"', cs);
            return Double.parseDouble(body.substring(cs, ce));
        } catch (Exception e) { return Double.NaN; }
    }

    private double fetchBinancePrice() { return fetchBtcPrice(); }

    private double fetchBinanceFunding() {
        try {
            HttpRequest req = HttpRequest.newBuilder(
                URI.create("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT"))
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int idx = body.indexOf("\"lastFundingRate\"");
            if (idx < 0) return 0;
            int cs = body.indexOf('"', idx + 18) + 1;
            int ce = body.indexOf('"', cs);
            return Double.parseDouble(body.substring(cs, ce));
        } catch (Exception e) { return 0; }
    }

    private double fetchBinanceOi() {
        try {
            HttpRequest req = HttpRequest.newBuilder(
                URI.create("https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"))
                .GET().build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int idx = body.indexOf("\"openInterest\"");
            if (idx < 0) return Double.NaN;
            int cs = body.indexOf('"', idx + 14) + 1;
            int ce = body.indexOf('"', cs);
            return Double.parseDouble(body.substring(cs, ce));
        } catch (Exception e) { return Double.NaN; }
    }

    private double fetchCoinGeckoVolume() {
        try {
            HttpRequest req = HttpRequest.newBuilder(
                URI.create("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true"))
                .GET().timeout(Duration.ofSeconds(10)).build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int idx = body.indexOf("\"usd_24h_vol\"");
            if (idx < 0) return Double.NaN;
            int cs = body.indexOf(':', idx + 13) + 1;
            int ce = body.indexOf(',', cs);
            if (ce < 0) ce = body.indexOf('}', cs);
            return Double.parseDouble(body.substring(cs, ce).trim());
        } catch (Exception e) { return Double.NaN; }
    }

    public double fetchBtcHistoricalPrice(LocalDate date) {
        long unix = date.atStartOfDay(ZoneOffset.UTC).toEpochSecond();
        try {
            HttpRequest req = HttpRequest.newBuilder(
                URI.create("https://api.coingecko.com/api/v3/coins/bitcoin/history?date="
                    + date.getDayOfMonth() + "-" + date.getMonthValue() + "-" + date.getYear()
                    + "&localization=false"))
                .GET().timeout(Duration.ofSeconds(10)).build();
            HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
            String body = resp.body();
            int idx = body.indexOf("\"usd\"");
            if (idx < 0) return Double.NaN;
            int cs = body.indexOf(':', idx + 5) + 1;
            int ce = body.indexOf(',', cs);
            if (ce < 0) ce = body.indexOf('}', cs);
            return Double.parseDouble(body.substring(cs, ce).trim());
        } catch (Exception e) { return Double.NaN; }
    }
}
