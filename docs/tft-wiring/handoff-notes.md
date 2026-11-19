# Nano / KMRTM24024-SPI — wiring handoff, revision B

**Status: conditional reference design; not approved for installation or power-up on the unmodified MR Innovative PCB.**

This package follows the hardware-SPI pin map in the supplied task. It supersedes the earlier chat's software-SPI map. Do not mix the two maps. The uploaded brief ends mid-sentence after “Left: Arduino Nano with individually labelled”; the rest of the page layout was chosen to make the wiring traceable.

Read [wiring-review.md](wiring-review.md) for the detailed schematic audit and corrected power/enable interpretation. The supplied hardware-SPI map remains conditional.

## Files

- `wiring-review.md`: detailed PCB/Nano/motor-driver review with a candidate software-SPI alternative.
- `Nano-TFT-wiring-A3.pdf`: two landscape A3 sheets, vector graphics with embedded fonts. Print at actual size.
- `signal-schematic-A3.svg`: editable vector signal drawing.
- `power-and-checks-A3.svg`: editable power/parts/checks sheet.
- `connection-netlist.json`: authoritative component and electrical net definition, including conditional links.
- `connections.csv`: readable net membership list.
- `rendered-wire-segments.json`: every drawn conductor, with page, net and coordinates.
- `validation-report.json`: programmatic checks and divider calculations.
- `build_wiring.py`: deterministic generator; requires Python and ReportLab. Adjust OUT to change the output folder.

No generative image tools were used. Resistor symbols are IEC rectangles. Filled dots are intentional junctions. Equal net names and GND symbols connect electrically; blank gaps at commissioning links mean open circuits. Labelled TFT pins are logical functions rather than an assumed connector orientation. T_OUT is the photograph's label for the task's T_DO.

## Why this is conditional

1. **Existing L298N:** the published PCB connects D7/D8/D10/D11 to L298N inputs 1/2/3/4. These are occupied pins, not spare SPI pins. Hardware SPI and control signals will toggle the L298N if left connected. Disconnecting motors alone does not isolate the inputs. Removing IC power alone risks back-powering. A technician must document physical logic isolation before this map is used; if the L298N remains needed for feeding, this allocation needs redesign rather than simply disabling it.
2. **A4988 enable:** D12 reaches both A4988 active-low enables through the two-pin EN link when that link is fitted. MISO must be an input and cannot share an actively controlled enable net. Verify/remove the EN link as a possible reversible isolation point, keep the driver-side enable safely defined, and assign a separate enable strategy. Do not cut traces without establishing the actual board routing and preserving the feeding plan. The older Stage 1 sketch explicitly drives D12 HIGH: it must not be used with MISO connected.
The original firmware's D9 enable controls BOTH L298N bridge enables, separately from D12/A4988. It is not a D9/D12 documentation mismatch.
3. **Remaining signals:** leave the encoder unplugged on D2/D4. Preserve D5/D6 for MG90S, A0-A3 for A4988 STEP/DIR, and D0/D1 for USB serial. D13 has no other load shown in the source PCB schematic, but Nano onboard LED loading still exists. Confirm the actual PCB revision by continuity.
4. **Power:** the task requests a regulated 3.3V TFT supply, which the drawing shows. That does not prove 3.3V on the module's VCC header reaches its internal rail correctly. Read the actual U1 marking and confirm J1's function first. A 3.3V input through an unbypassed regulator can produce too little voltage. Do not bridge a jumper based only on its name.
5. **Backlight:** LED supply/current limiting is unverified. JP2 stays open until the backlight arrangement is confirmed. A bare LED string needs controlled current; it must not be assumed to have an onboard resistor or connected to a Nano GPIO.
6. **Chip identities:** the photo identifies the connector labels, not the exact LCD and touch controller silicon. ILI9341/XPT2046 are possibilities, not verified identities. Select libraries only after identification.

## Supply rail correction

The MR drawing uses distinct `5V` (Nano output, including ENCODER/I2C/HC-05 and motor logic supplies) and `+5V` (two paralleled 7805 outputs, servo selector and pots). Do not assume the header 5V comes from the servo regulators or add the two 7805 current ratings together. The drawing also marks A1/A3 STEP pull-downs as 200 ohms: inspect actual fitted values before driving them. See the detailed review for measurements and implications.

## Divider calculation — six channels, not five

Use one 1k upper and one 2k lower resistor per Nano output: CS, RESET, D/C, MOSI, SCK and touch CS. RESET adds a sixth channel compared with the earlier provisional chat wiring. Shared MOSI and clock each use one divider followed by a branch, not separate dividers per destination.

Vout = Vin × Rlower / (Rupper + Rlower).

- 5.00V, nominal resistance: 3.333V.
- Illustrative worst-case Vin=5.25V, ±1%: 5.25 × 2020/(990+2020) = 3.523V.
- Illustrative worst-case Vin=5.25V, ±5%: 5.25 × 2100/(950+2100) = 3.615V.

5.25V is an explicit analysis assumption, not a measured ceiling for this Nano. Recalculate from actual supply bounds and resistor tolerances. Input leakage, shared-input capacitance, ground bounce and edge overshoot add further uncertainty.

For an **ILI9341 example**, Section 18.2 lists the recommended input-high upper limit as VDDI, while Section 18.1 specifies the absolute maximum at VDDI+0.3V. Nominal 3.333V already exceeds a 3.300V recommended input ceiling. The 5% worst case exceeds even 3.600V. With an illustrative 3.3V rail at −5%, the absolute ceiling is 3.435V, below the 1% divider worst case. Absolute maxima are not design operating targets. When the TFT is unpowered, driven inputs also risk injecting current.

**Conclusion:** the requested 1k/2k dividers are faithfully drawn for review but cannot be approved as a guaranteed-compliant ILI9341 interface under these assumptions. This corrects the earlier chat's overly broad assurance about resistor-divider suitability.

### Preferred output conversion

Replace all six dividers with six channels of a **TI SN74LVC245A**, powered from the TFT's verified 3.3V logic rail, with common GND, DIR HIGH (A to B), /OE LOW when operation is allowed, and a 100nF bypass capacitor at its supply pins. Its inputs accept up to 5.5V. Use the exact package pinout; do not substitute a generic HC245. Hold unused inputs at defined levels. Each original independent signal gets a channel; the clock/MOSI outputs then branch exactly as drawn. This is an alternative implementation, not something to add in series with the dividers. Sequence/enable control must prevent signal injection when supplies are absent.

## Readback and shared MISO

JP3 (display SDO), JP4 (touch T_OUT) and optional JP5 (IRQ) are normally open. Confirm the chips release their outputs when their own CS is inactive before closing both JP3 and JP4. Both CS lines need known inactive states during normal transactions; initialize CS HIGH before SPI and before enabling actuators. Dividers pull CS low when Nano outputs float, so boot behavior needs explicit consideration.

The task's direct 3.3V-return-to-Nano connection is also conditional. For typical ATmega328P GPIO, VIH is at least 0.6×VCC: 3.0V at 5.0V and 3.15V at 5.25V. The actual peripheral's **guaranteed VOH**, not just its supply voltage, must exceed the Nano threshold. For example, ILI9341's 0.8×VDDI bound can be below it. Use a suitable **5V SN74AHCT125** return buffer where margins fail. It has TTL-compatible inputs; use the actual data sheet to verify all thresholds. Up-shifting does not solve two peripherals driving MISO simultaneously.

If display SDO does not release the bus, leave JP3 open and use touch-only readback after verifying JP4's voltage margins. T_IRQ is optional; polling may avoid JP5 entirely. Leave SD-card pins unused.

## Parts explanation

| Item | Quantity | Purpose / requirement |
|---|---:|---|
| Existing Nano, MR PCB and TFT | 1 each | Reused hardware; preserve servo and feeding connections |
| 1kΩ, 1%, ≥0.125W | 6 | Upper divider resistors; conditional implementation |
| 2kΩ, 1%, ≥0.125W | 6 | Lower divider resistors to common ground |
| Complete 3.3V buck module | 1 | Rated for 12V input and ≥500mA continuous; verify real load/thermal capacity |
| 100nF ceramic, ≥10V | 1 | Local TFT VCC bypass, in addition to module-required capacitors |
| 10µF, ≥10V | 1 | Local TFT VCC bulk bypass; observe polarity if polarized |
| Removable commissioning links | Up to 5 | Leave power, backlight and return connections open until their conditions are met |
| Breadboard and short jumper wires | As needed | Low-speed prototype signals; keep servo current out of signal-ground paths |
| Multimeter; oscilloscope/logic analyzer | As available | Voltage, continuity, edge integrity and bus-release checks |
| SN74LVC245A + 100nF | Alternative | Six-channel 5V-to-3.3V output conversion, replacing all resistor pairs |
| SN74AHCT125 + 100nF | If required | 3.3V-return to 5V-input margin correction; exact connection design must be checked |

The **AP63203QWU-7 is an IC**, not a ready-to-wire regulator. A complete module is the simpler construction choice. A custom implementation needs a PCB following the manufacturer's current reference design: inductor selection, input/output/bootstrap capacitors, feedback sense, enable connections and switching-loop layout. Do not assemble the raw switching-regulator circuit on a solderless breadboard. The drawing intentionally treats a qualified complete buck module as a functional block; it does not invent an unverified AP63203Q bill of materials.

All power grounds connect, but route servo/motor currents back separately so they do not flow through the TFT/divider ground wiring. The new 3.3V output must not connect to Nano 5V, the servo supply, or the Nano's existing 3.3V output. Never put 12V on the TFT header.

## Commissioning sequence / acceptance

1. Remove 12V and USB. Identify ICs, jumpers and connector orientation. Document all PCB logic isolation and confirm it with a meter; preserve a defined A4988 enable state.
2. Resolve signal conversion in both directions against actual data sheets. Do not power from this conditional divider drawing until those margins are resolved.
3. Keep JP1-JP5 open. Check for shorts, verify common ground, set the buck to 3.3V and confirm polarity before attaching its load. Check actual display rail voltage/current with the validated module configuration.
4. Close power/backlight links only after their conditions are satisfied. With all actuators isolated, test display-only operation at a deliberately low SPI clock (start around 100kHz and verify edges). No direct connection is implied across an open jumper in the drawing.
5. Verify high-impedance MISO behavior with suitable bus measurements; then connect approved return paths and test touch. A logic analyzer alone does not prove absence of output contention.
6. Only then integrate matching firmware; remove the previous D12-output initialization. Confirm separate CS behavior, readable graphics, stable touch, valid voltages and no resets before restoring actuator operation.

No firmware is included or uploaded. This documentation does not certify the cutter mechanisms or declare Stage 1 cutting acceptance complete.

## Sources

- Original project: https://electricdiylab.com/diy-arduino-based-resistor-reel-cutting-machine/
- Original multipurpose PCB schematic, Rev 1.0 dated 2021-01-22: https://electricdiylab.com/wp-content/uploads/2021/05/bcc35e9a4fae493bbf922772c43afde7.png
- ILI Technology ILI9341 data sheet (manufacturer document hosted by Adafruit), Sections 18.1/18.2, PDF pages 235–236: https://cdn-shop.adafruit.com/datasheets/ILI9341.pdf
- TI SN74LVC245A: https://www.ti.com/product/SN74LVC245A
- TI SN74AHCT125: https://www.ti.com/product/SN74AHCT125
- Diodes AP63203Q: https://www.diodes.com/part/view/AP63203Q
- Diodes reference evaluation-board guide: https://www.diodes.com/assets/Evaluation-Boards/AP63203QWU-EVM-User-Guide.pdf

## Validation scope

The generator checks unique endpoint-to-net assignment, six divider channels, required shared branches, protected D5/D6, mandated pin roles, orthogonal wire segments, and zero unintended crossings/overlaps between different named nets. PDFs were rendered and inspected. These checks verify the drawing and its explicit design definition, not the unseen actual hardware or its unresolved electrical conditions.
