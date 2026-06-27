package com.tradingtabs.engine;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

@DisplayName("BtcFrame assessment")
class BtcFrameTest {

    @Nested
    @DisplayName("GREEN scenario — bullish BTC")
    class GreenScenario {

        @Test
        @DisplayName("returns GREEN when price above MA, funding neutral, momentum positive")
        void bullishSignals() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(70000)
                .withBtcHistory(List.of(60000.0, 62000.0, 64000.0, 66000.0, 68000.0, 70000.0))
                .withBtcFunding(0.00005)
                .withBtcVolume(30_000_000_000.0)
                .withBtcOi(15_000_000_000.0)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.status()).isEqualTo("GREEN");
        }
    }

    @Nested
    @DisplayName("RED scenario — bearish BTC")
    class RedScenario {

        @Test
        @DisplayName("returns RED when price deep below MA, momentum negative")
        void bearishSignals() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(40000)
                .withBtcHistory(List.of(60000.0, 55000.0, 50000.0, 45000.0, 42000.0, 40000.0))
                .withBtcFunding(-0.0005)
                .withBtcVolume(5_000_000_000.0)
                .withBtcOi(15_000_000_000.0)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.status()).isEqualTo("RED");
        }
    }

    @Nested
    @DisplayName("Edge cases")
    class EdgeCases {

        @Test
        @DisplayName("returns YELLOW when no price data")
        void noPriceData() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(Double.NaN)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.status()).isEqualTo("YELLOW");
            assertThat(result.explanation()).contains("no BTC price data");
        }

        @Test
        @DisplayName("returns YELLOW when price is zero")
        void zeroPrice() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(0)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.status()).isEqualTo("YELLOW");
        }
    }

    @Nested
    @DisplayName("Support and resistance levels")
    class SupportResistance {

        @Test
        @DisplayName("support levels are below fair value")
        void supportBelowFair() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(65000)
                .withBtcHistory(List.of(60000.0, 62000.0, 64000.0, 65000.0))
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.support1()).isLessThan(result.fairValue());
            assertThat(result.support2()).isLessThan(result.support1());
        }

        @Test
        @DisplayName("resistance levels are above fair value")
        void resistanceAboveFair() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcPrice(65000)
                .withBtcHistory(List.of(60000.0, 62000.0, 64000.0, 65000.0))
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.resistance1()).isGreaterThan(result.fairValue());
            assertThat(result.resistance2()).isGreaterThan(result.resistance1());
        }
    }

    @Nested
    @DisplayName("Funding rate analysis")
    class FundingRate {

        @Test
        @DisplayName("positive funding rate gives positive Z-score")
        void positiveFunding() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcFunding(0.0005)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.fundingZ()).isPositive();
        }

        @Test
        @DisplayName("negative funding rate gives negative Z-score")
        void negativeFunding() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcFunding(-0.0005)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.fundingZ()).isNegative();
        }

        @Test
        @DisplayName("neutral funding rate gives zero Z-score")
        void neutralFunding() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withBtcFunding(0.00005)
                .build();

            BtcFrame.BtcResult result = new BtcFrame(snap).assess();

            assertThat(result.fundingZ()).isZero();
        }
    }
}
