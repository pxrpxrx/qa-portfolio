package com.tradingtabs.engine;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

@DisplayName("DivergenceScanner")
class DivergenceScannerTest {

    @Nested
    @DisplayName("DXY and BTC divergences")
    class DxyBtcDivergences {

        @Test
        @DisplayName("detects DXY up + BTC up as fragile risk-on")
        void dxyUpBtcUp() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDxyHistory(List.of(103.0, 103.5, 104.0, 104.5, 105.0, 105.5))
                .withBtcHistory(List.of(60000.0, 61000.0, 62000.0, 63000.0, 64000.0, 65000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).anyMatch(d ->
                d.label().contains("DXY up") && d.label().contains("BTC up")
            );
        }

        @Test
        @DisplayName("detects DXY down + BTC up as classic risk-on")
        void dxyDownBtcUp() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDxyHistory(List.of(105.5, 105.0, 104.5, 104.0, 103.5, 103.0))
                .withBtcHistory(List.of(60000.0, 61000.0, 62000.0, 63000.0, 64000.0, 65000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).anyMatch(d ->
                d.label().contains("DXY down") && d.label().contains("BTC up")
            );
        }

        @Test
        @DisplayName("detects DXY up + BTC down as risk-off flight")
        void dxyUpBtcDown() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDxyHistory(List.of(103.0, 103.5, 104.0, 104.5, 105.0, 105.5))
                .withBtcHistory(List.of(65000.0, 64000.0, 63000.0, 62000.0, 61000.0, 60000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).anyMatch(d ->
                d.label().contains("DXY up") && d.label().contains("BTC down")
            );
        }
    }

    @Nested
    @DisplayName("M2 and BTC divergences")
    class M2BtcDivergences {

        @Test
        @DisplayName("detects M2 up + BTC down as potential reversal")
        void m2UpBtcDown() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(20.0, 20.2, 20.5, 20.8, 21.0, 21.2))
                .withBtcHistory(List.of(65000.0, 64000.0, 63000.0, 62000.0, 61000.0, 60000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).anyMatch(d ->
                d.label().contains("M2 up, BTC down")
            );
            assertThat(divs).anyMatch(d ->
                d.label().contains("M2 up, BTC down") && !d.bearish()
            );
        }

        @Test
        @DisplayName("detects M2 down + BTC up as fragile")
        void m2DownBtcUp() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(21.2, 21.0, 20.8, 20.5, 20.2, 19.8))
                .withBtcHistory(List.of(60000.0, 61000.0, 62000.0, 63000.0, 64000.0, 65000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).anyMatch(d ->
                d.label().contains("M2 down, BTC up")
            );
            assertThat(divs).anyMatch(d ->
                d.label().contains("M2 down, BTC up") && d.bearish()
            );
        }
    }

    @Nested
    @DisplayName("No divergence scenarios")
    class NoDivergence {

        @Test
        @DisplayName("returns empty list when no divergences detected")
        void noDivergences() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDxyHistory(List.of(104.0, 104.0, 104.0, 104.0, 104.0, 104.0))
                .withBtcHistory(List.of(65000.0, 65000.0, 65000.0, 65000.0, 65000.0, 65000.0))
                .withM2History(List.of(21.0, 21.0, 21.0, 21.0, 21.0, 21.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            assertThat(divs).isEmpty();
        }
    }

    @Nested
    @DisplayName("Divergence properties")
    class DivergenceProperties {

        @Test
        @DisplayName("all divergences have non-empty label")
        void nonEmptyLabel() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDxyHistory(List.of(103.0, 103.5, 104.0, 104.5, 105.0, 105.5))
                .withBtcHistory(List.of(60000.0, 61000.0, 62000.0, 63000.0, 64000.0, 65000.0))
                .build();

            List<DivergenceScanner.Divergence> divs = new DivergenceScanner(snap).scan();

            for (DivergenceScanner.Divergence d : divs) {
                assertThat(d.label()).isNotEmpty();
                assertThat(d.description()).isNotEmpty();
            }
        }
    }
}
