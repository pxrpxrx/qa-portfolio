package com.tradingtabs.model;

import java.time.LocalDate;

public class Prediction {
    public final LocalDate date;
    public final double btcPriceTarget;
    public final double btcLowerBound;
    public final double btcUpperBound;
    public final double confidence;       // 0.0–1.0
    public final Direction direction;
    public final String signal;
    public final double resonanceScore;
    public final double gannAngle;

    public enum Direction { BULLISH, BEARISH, NEUTRAL }

    public Prediction(LocalDate date, double target, double lower, double upper,
                      double confidence, Direction dir, String signal,
                      double resonance, double gannAngle) {
        this.date = date;
        this.btcPriceTarget = target;
        this.btcLowerBound = lower;
        this.btcUpperBound = upper;
        this.confidence = confidence;
        this.direction = dir;
        this.signal = signal;
        this.resonanceScore = resonance;
        this.gannAngle = gannAngle;
    }

    public String toLine() {
        return String.format("[%s] %s BTC=%.0f (%.0f–%.0f) | confidence=%.0f%% | %s | res=%.2f | gann=%.1f°",
            date, direction, btcPriceTarget, btcLowerBound, btcUpperBound,
            confidence * 100, signal, resonanceScore, gannAngle);
    }
}
