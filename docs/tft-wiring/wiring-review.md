# Wiring review — MR Innovative PCB, Nano and motor drivers

**Review date: 20 November 2026. Result: do not install the proposed hardware-SPI wiring unchanged.**

The review compares the original PCB drawing, original cutter firmware, Arduino Nano V3.3 schematic/pinout, ST L298 data sheet, Allegro A4988 data sheet and carrier documentation. It is a schematic review, not an inspection or measurement of the assembled PCB. The exact TFT controller, touch controller, onboard regulator, jumper configuration and actual PCB component population remain unverified.

## Findings, ordered by consequence

### 1. Hardware SPI overlaps existing motor control — confirmed from the PCB drawing

The proposed D10/D7/D8/D11 display outputs also drive the L298N. The motor driver may respond to screen commands if those connections remain. D12 has a separate conflict when the PCB's two-pin EN link is fitted. Keeping the motors unplugged is useful for initial testing but does not make this a suitable permanent shared-pin arrangement.

| Nano signal | Connection in original PCB schematic | Proposed hardware-SPI use | Review |
|---|---|---|---|
| D0/D1 | HC-05/serial header and Nano USB serial circuit | None | Keep available for Serial Monitor |
| D2 | ENCODER pin 4 | Optional touch IRQ | Only available if encoder / original serial HMI is absent |
| D3 | ENCODER pin 5 | None in hardware-SPI drawing | Available under same condition |
| D4 | ENCODER pin 3 | Touch CS | Acceptable if encoder absent |
| D5 | SERVO01 pin 3 | None | Preserve confirmed cutter signal |
| D6 | SERVO02 pin 3 | None | Preserve confirmed cutter signal |
| D7 | L298N input 1, IC pin 5 | TFT RESET | Conflict |
| D8 | L298N input 2, IC pin 7 | TFT D/C | Conflict |
| **D9** | **L298N Enable A and Enable B, IC pins 6 and 11** | None | Occupied; active HIGH, LOW disables both bridges |
| D10 | L298N input 3, IC pin 10 | TFT CS | Conflict |
| D11 | L298N input 4, IC pin 12 | SPI MOSI | Conflict |
| **D12** | **Nano to EN-link pin 1; link pin 2 goes to both A4988 enables** | SPI MISO | Conflict when EN link is fitted; verify actual continuity |
| D13 | No external load in MR drawing; LED on official Nano | SPI SCK | Available as output, subject to actual clone wiring |
| A0 | First A4988 DIR | None | Preserve |
| A1 | First A4988 STEP | None | Preserve; check pull-down value below |
| A2 | Second A4988 DIR | None | Preserve |
| A3 | Second A4988 STEP | None | Preserve; check pull-down value below |
| A4/A5 | I2C header pins 3/4 | None | Can be GPIO if I2C devices absent |
| A6/A7 | POT1/POT2 wipers | None | Analog-input-only on classic Nano; not spare SPI GPIO |

### 2. D9 and D12 control different drivers — correction to earlier advice

Earlier chat described the original firmware's `EN=9` versus schematic D12 as a discrepancy. That was incomplete: **D9 controls the L298N enables; D12 is the separate A4988-enable connection through the EN link.** The original firmware's D9 HIGH enables the L298N and is consistent with its feeding control. It does not establish A4988 enable state.

The previous Stage 1 sketch drives D12 HIGH, which only disables the A4988 outputs if the physical EN link is fitted and the PCB matches the drawing. It leaves D9 unconfigured. Do not assume that sketch disables every motor driver. In a later integrated sketch, initialize D9 LOW, and D12 HIGH with its confirmed link arrangement, before enabling actuators. These are firmware requirements, not changes uploaded during this review.

If hardware-SPI MISO is retained on D12, the EN link offers a possible reversible isolation point. Confirm the connector orientation and continuity with power removed. Do not cut a PCB trace merely because earlier notes said to isolate the net. Removing the link does not itself provide a defined disabled state on the A4988 side: arrange an appropriate pull-up to its own VDD and a separate planned enable strategy. Permanent always-disabled drivers will not support feeding.

### 3. `5V` and `+5V` are separate rails in the published schematic

| Rail | Drawing's source | Drawing's loads |
|---|---|---|
| VCC | 12V input after the 1N5408 protection diode | A4988 VMOT, regulator inputs, selectable L298N motor supply |
| +9V | 7809 output | Nano VIN, optional L298N motor supply, optional servo supply |
| **5V** | **Nano 5V pin, normally its onboard regulator when VIN is supplied** | **ENCODER/HC-05/I2C 5V header pins, A4988 VDD/microstep jumpers, L298N VSS** |
| **+5V** | **Two 7805 outputs drawn tied together** | **Servo 5V/9V selector and potentiometer supply** |

Therefore the convenient ENCODER/I2C 5V pins are not shown as the output of the pair of board 7805s. Loading those headers can heat the **Nano's** regulator. Read the actual regulator/USB-interface markings on the installed Nano; clones can differ from Arduino's official schematic.

The two 7805 outputs are visibly connected in parallel in the source drawing. Ordinary independent 7805s do not guarantee equal current sharing. **Do not add their nameplate current ratings together.** Verify actual population and connections before deciding what the servo rail can supply. Existing servo movement proves function, not full-load electrical margin.

At about 11.3V after the input diode, 0.5A into a linear 5V supply implies approximately (11.3−5)×0.5 = 3.15W total regulator dissipation, not necessarily equally shared. This is an illustrative estimate, not a measured board temperature or available-current rating. A dedicated suitably rated buck supply is preferable for servo loads once actual peak current is established; isolate the old positive feed before substituting a supply, while retaining common ground.

### 4. STEP pull-down resistors are labelled 200Ω — verify before feeding work

The MR drawing labels R1 and R2 as **200**, connected from A1/STEP and A3/STEP to ground. If those really are 200Ω, each HIGH output is loaded by roughly 5/200 = **25mA**, before the driver input current. Arduino's Nano pinout specifies 20mA per I/O pin. This is an excessive design load and can reduce output voltage margin.

This may be a documentation or population error; do not declare the actual resistors wrong without inspecting them. With all power removed, use the fitted markings and isolated resistance measurement as needed; in-circuit parallel paths can distort a reading. A conventional high-value pull-down such as 10kΩ would draw only 0.5mA, but any replacement must be checked against the actual circuit. Do not test a suspected 200Ω load by deliberately holding that Nano output HIGH.

### 5. The TFT supply and signal conversion remain unresolved

The six-divider drawing correctly branches one divided clock to SCK/T_CLK and one divided MOSI to SDI/T_DIN. Separate display/touch chip selects are also required. However, the nominal 1k/2k output is 3.333V at a 5.000V input, and worst-case voltage can exceed the actual display input ratings. The existing handoff calculations remain applicable. Use the actual LCD data sheet; do not design to its absolute maximum.

A suitable SN74LVC245A powered from the verified TFT logic rail is the preferred down-conversion alternative. MISO/IRQ return signals also need guaranteed input-high margin at the 5V AVR; do not assume every 3.3V peripheral output satisfies it. Shared MISO additionally needs verified high-impedance behavior when deselected. Readback can be simplified by leaving display SDO unconnected and reading touch only.

The proposed regulated 3.3V source is not yet permission to connect 3.3V to the module's VCC header: verify onboard U1/J1 bypass requirements. LED current limiting remains unverified. The Nano's official 3.3V pin limit is 50mA; it is not an assumed supply for the TFT/backlight. A raw AP63203QWU-7 still needs its complete reference circuit and PCB layout.

### 6. Driver power details need checking on the actual build

- Check A4988 carrier orientation and labels, not the IC's 28-pin numbering: the MR schematic uses a **16-pin carrier symbol**. The installed carriers may be clones with different sense resistors.
- VMOT and VDD are different supplies: A4988 VMOT uses the post-diode motor rail, VDD uses the Nano 5V rail. Do not put 12V on VDD.
- RESET and SLEEP are tied together in each schematic carrier position. Verify the installed carrier's pull-up arrangement; do not leave this pair at an undefined voltage. The PCB drawing alone does not show all components on a carrier.
- Confirm a defined STEP/DIR state and all microstep jumper settings before determining steps per resistor. Set current limit using the carrier's actual sense resistance and motor rating, not an assumed universal VREF value.
- Check local VMOT decoupling. The main input's 100uF and the L298N's 47uF are not proof of adequate local A4988 suppression. Carrier guidance recommends at least 47uF near VMOT/GND for LC-spike protection. Never plug/unplug a stepper while powered.
- L298N's sense pins are grounded in this drawing; there is no shown adjustable stepper-current chopper for its motor. Do not assume its L298N-fed stepper has A4988-like current regulation. Motor resistance, supply, heating and bridge voltage loss matter.
- L298N needs local bypassing at VS and VSS. The MR drawing does not show the data sheet's small local capacitors; inspect whether they exist on the physical assembly before concluding they are missing.

## Recommended direction: preserve the PCB and use software SPI

For retaining all original motor-control connections, prefer the spare ENCODER/I2C signals plus D13 instead of the supplied hardware-SPI map. The following is a **candidate allocation**, not a finalized electrical wiring instruction:

| Function | Candidate Nano connection | Access |
|---|---|---|
| Software SPI clock: SCK and T_CLK | D13 | Nano pin |
| Software SPI MOSI: SDI and T_DIN | D3 | ENCODER pin 5 |
| TFT CS | A4 | I2C pin 3 |
| TFT D/C | A5 | I2C pin 4 |
| Touch CS | D4 | ENCODER pin 3 |
| Touch data return: T_OUT | D2 | ENCODER pin 4 |
| TFT RESET | Buffered Nano RESET, or a separately designed reset circuit | Nano RESET pin; confirm sequencing |
| Display SDO / touch IRQ / SD card | Unconnected | No display readback; touch polled |

All Nano-to-TFT control signals still require suitable conversion; a buffer can translate Nano RESET without consuming another GPIO. Validate reset sequencing and the actual module reset specification before implementing this. The return signal may need a 3.3V-to-5V buffer. This map leaves D7-D12, A0-A3, D5/D6 and USB serial available for their existing functions. No encoder, HC-05/original serial HMI on D2/D3, or I2C peripherals can share these reassigned pins. A matching software-SPI display and touch implementation is required; a default hardware-SPI library configuration will not work.

**No trace cuts, replacement components, new wiring or firmware uploads have been performed.** The review does not declare Stage 1 cutting acceptance complete.

## Practical next checks

1. Photograph actual PCB top/bottom, installed Nano, regulator markings, EN link and driver carriers. Compare fitted components with this source drawing.
2. Power removed: confirm D9 to L298N pins 6/11, EN-link topology, A1/A3 pull-down values, and separation of Nano `5V` from servo `+5V`. Use isolated measurements where semiconductor paths make continuity ambiguous. Never bridge the rails merely to test them.
3. Confirm TFT U1 marking, J1 state, LCD/touch IC identities and LED current limiting.
4. Choose the software-SPI candidate if preserving the original PCB is the goal; then issue a new implementable schematic based on the verified components and level conversion. Do not assemble the old hardware-SPI design unchanged.

## Primary references

1. [MR Innovative project and original firmware](https://electricdiylab.com/diy-arduino-based-resistor-reel-cutting-machine/)
2. [MR multipurpose PCB source schematic, revision 1.0, 2021-01-22](https://electricdiylab.com/wp-content/uploads/2021/05/bcc35e9a4fae493bbf922772c43afde7.png)
3. [Arduino Nano official V3.3 schematic](https://content.arduino.cc/assets/NanoV3.3_sch.pdf)
4. [Arduino Nano official pinout and current limits](https://docs.arduino.cc/resources/pinouts/A000005-full-pinout.pdf)
5. [ST L298 data sheet, pin functions and enable behavior](https://www.st.com/resource/en/datasheet/l298.pdf)
6. [Allegro A4988 data sheet, logic supply/input thresholds and enables](https://www.allegromicro.com/~/media/Files/Datasheets/A4988-Datasheet.pdf)
7. [Pololu A4988 carrier wiring, decoupling and current-limit guidance](https://www.pololu.com/product/1182) — carrier-specific guidance, not proof that these exact carriers are installed.
8. [ST L78 family data sheet, thermal and output regulation specifications](https://www.st.com/resource/en/datasheet/l78.pdf) — representative regulator data, not identification of actual fitted parts.
9. [ILI9341 manufacturer data sheet, sections 18.1/18.2](https://cdn-shop.adafruit.com/datasheets/ILI9341.pdf)

The source images and component documents establish the drawn circuit. Only physical inspection and measurements can establish whether the assembled PCB matches it.
