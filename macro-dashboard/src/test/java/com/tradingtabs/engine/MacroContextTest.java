package com.tradingtabs.engine;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.*;

@DisplayName("MacroContext assessment")
class MacroContextTest {

    @Nested
    @DisplayName("GREEN scenario — bullish macro")
    class GreenScenario {

        @Test
        @DisplayName("returns GREEN when M2 growing, curve normal, DXY weak, HYG tight")
        void allGreenSignals() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(20.0, 20.2, 20.5, 20.8, 21.0, 21.2))
                .withDgs10(4.5)
                .withDgs3mo(3.8)
                .withDxyHistory(List.of(105.0, 104.8, 104.5, 104.0, 103.5, 103.0))
                .withBaa10y(1.5)
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.status()).isEqualTo("GREEN");
        }
    }

    @Nested
    @DisplayName("RED scenario — bearish macro")
    class RedScenario {

        @Test
        @DisplayName("returns RED when M2 shrinking, curve inverted, DXY strong, HYG stress")
        void allRedSignals() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(21.0, 20.8, 20.5, 20.2, 20.0, 19.8))
                .withDgs10(3.5)
                .withDgs3mo(4.5)
                .withDxyHistory(List.of(103.0, 103.5, 104.0, 104.5, 105.0, 105.5))
                .withBaa10y(6.5)
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.status()).isEqualTo("RED");
        }
    }

    @Nested
    @DisplayName("YELLOW scenario — mixed signals")
    class YellowScenario {

        @Test
        @DisplayName("returns YELLOW when signals are mixed")
        void mixedSignals() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(21.0, 21.0, 21.0, 21.0, 21.0, 21.0))
                .withDgs10(4.0)
                .withDgs3mo(4.0)
                .withDxyHistory(List.of(104.0, 104.0, 104.0, 104.0, 104.0, 104.0))
                .withBaa10y(3.5)
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.status()).isEqualTo("YELLOW");
        }
    }

    @Nested
    @DisplayName("Individual factors")
    class IndividualFactors {

        @Test
        @DisplayName("M2 momentum is calculated correctly")
        void m2Momentum() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2History(List.of(20.0, 20.5, 21.0))
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.m2Momentum()).isPositive();
        }

        @Test
        @DisplayName("term spread is DGS10 minus DGS3MO")
        void termSpread() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withDgs10(4.5)
                .withDgs3mo(3.8)
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.termSpread()).isCloseTo(0.7, within(0.01));
        }

        @Test
        @DisplayName("net liquidity = M2 - TGA - ON RRP")
        void netLiquidity() {
            DataManager.Snapshot snap = new SnapshotBuilder()
                .withM2(21.5)
                .withTga(0.8)
                .withOnrrp(0.1)
                .build();

            MacroContext.MacroResult result = new MacroContext(snap).assess();

            assertThat(result.netLiquidity()).isCloseTo(20.6, within(0.01));
        }

        @Test
        @DisplayName("explanation is not empty")
        void explanationNotEmpty() {
            DataManager.Snapshot snap = new SnapshotBuilder().build();
            MacroContext.MacroResult result = new MacroContext(snap).assess();
            assertThat(result.explanation()).isNotEmpty();
        }
    }
}
