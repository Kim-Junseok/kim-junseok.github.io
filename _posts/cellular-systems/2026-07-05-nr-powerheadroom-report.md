---
title: "NR Power Headroom Report (2/3): What Does PHR Tell the gNB?"
description: "How NR calculates power headroom, distinguishes Type 1, Type 2, and Type 3 PH, and reports real or reference transmissions through a PHR MAC CE."
date: 2026-07-05
math: true
categories: [Cellular Systems, 5G NR]
tags:
  - 5G NR
  - PHR
  - Power Headroom
  - MAC CE
  - PUSCH
---

> **NR Uplink Power Control and PHR Series**
>
> 1. [Power Budget, PSD, and `P_CMAX`]({{ '/posts/uplink-power-control-basics/' | relative_url }})
> 2. **What Does a Power Headroom Report Tell the gNB?**
> 3. [How a gNB Scheduler Uses PHR]({{ '/posts/nr-phr-gnb-scheduling/' | relative_url }})

In the [previous article]({{ '/posts/uplink-power-control-basics/' | relative_url }}), we summarized PUSCH transmit power with the following structure:

$$
P_{\text{actual}}
=
\min
\{
P_{\text{CMAX}},
P_{\text{required}}
\}
$$

The gNB cannot directly observe the UE's internal power budget. Instead, the UE uses a Power Headroom Report (PHR) to indicate how much margin remains before it reaches its maximum power for a real or reference uplink transmission.

---

## 1. What Does PH Mean?

An intuitive expression for Type 1 power headroom is:

$$
PH
=
P_{\text{CMAX}}
-
P_{\text{required}}
$$

- `PH > 0`: The UE has margin above the power required by the power-control equation.
- `PH ≈ 0`: The UE is near its maximum power.
- `PH < 0`: The required power exceeds the maximum power.

For example, suppose:

$$
P_{\text{CMAX}}
=
23\text{ dBm}
$$

and:

$$
P_{\text{required}}
=
18\text{ dBm}
$$

The power headroom is 5 dB:

$$
PH
=
23 - 18
=
5\text{ dB}
$$

If the required power were 26 dBm instead, the PH would be -3 dB. This does **not** mean that the UE actually transmitted at 26 dBm. Its actual transmit power may be capped by `P_CMAX`; PH represents the difference between the nominal maximum power and the estimated required power.

---

## 2. Type 1 PH

Type 1 PH is the power headroom for **UL-SCH/PUSCH transmission** on an activated serving cell.

A simplified expression based on a real PUSCH transmission is:

$$
PH_{\text{type1,real}}
=
P_{\text{CMAX}}
-
\left\{
P_O
+
10\log_{10}(2^\mu M_{\text{RB}})
+
\alpha PL
+
\Delta_{TF}
+
f
\right\}
$$

Here, `M_RB`, `Δ_TF`, and the power-control adjustment reflect the conditions of the real PUSCH transmission.

A real Type 1 PH therefore answers a question close to:

> Given this PUSCH grant, how much power headroom does the UE have left?

Type 1 is the PH type most directly related to PUSCH scheduling.

---

## 3. Type 2 and Type 3 PH

The three PH types are not simply generic categories for every uplink channel. Each type needs to be understood together with the deployment and transmission for which it is defined.

| Type | Basis | Meaning |
|---|---|---|
| Type 1 | UL-SCH/PUSCH | PUSCH power headroom for an activated serving cell |
| Type 2 | SpCell of the other MAC entity | Power headroom related to UL-SCH and PUCCH transmission on the other MAC entity's SpCell in EN-DC, NE-DC, and NGEN-DC |
| Type 3 | SRS | SRS power headroom for an activated serving cell |

It would be too broad to describe Type 2 simply as “PH when PUSCH and PUCCH are transmitted simultaneously” on an ordinary NR serving cell. Following the definition in TS 38.321, it is more accurate to identify Type 2 as **the PH type associated with the SpCell of the other MAC entity in dual-connectivity scenarios**.

Because Type 3 is based on SRS transmission, it can help characterize uplink sounding and the associated power conditions.

---

## 4. Real Transmissions and Reference Formats

A PHR may be required even when a serving cell has no real PUSCH or SRS transmission at that moment. In that case, the UE can calculate PH using a reference format defined by the specifications.

| PH type | Real-transmission basis | Reference basis |
|---|---|---|
| Type 1 | Real PUSCH | PUSCH reference format |
| Type 2 | Real PUCCH | PUCCH reference format |
| Type 3 | Real SRS | SRS reference format |

Conceptually, Type 1 reference PH can be written as:

$$
PH_{\text{type1,reference}}
=
\widetilde{P}_{\text{CMAX}}
-
\left\{
P_O
+
\alpha PL
+
f
\right\}
$$

Because this calculation does not use a real PUSCH allocation, it is not based on the `M_RB` and `Δ_TF` of an actual grant. Reference PH is therefore best understood as:

> A headroom estimate calculated under specification-defined reference PUSCH conditions

The term **reference PH** is preferable here to the potentially ambiguous expression “virtual PH.”

---

## 5. `phr-ModeOtherCG = virtual` Is a Different Concept

Dual connectivity introduces a separate setting called `phr-ModeOtherCG`.

When this setting is `virtual`, the UE calculates PH for one cell group under the assumption that no PUSCH or PUCCH is transmitted in the other cell group.

This virtual condition is distinct from using a reference format because a serving cell has no real transmission.

| Situation | Meaning |
|---|---|
| No real transmission | Calculate PH using the reference format for that PH type |
| `phr-ModeOtherCG = virtual` | Calculate PH assuming no uplink transmission in the other cell group |

Calling both cases “virtual PHR” obscures which assumption the scheduler should apply.

---

## 6. When Is a PHR Triggered?

PHR is not continuous, per-slot telemetry. RRC configures the reporting behavior, and MAC transmits a PHR MAC CE when a trigger condition is met and an uplink grant is available.

Representative triggers include:

- Expiry of `phr-PeriodicTimer`
- A path-loss change greater than the configured threshold when the `phr-ProhibitTimer` condition is satisfied
- Configuration or reconfiguration of PHR functionality
- Activation of an SCell with configured uplink resources
- Certain multi-connectivity events, such as SCG activation or PSCell addition

The PH received by the gNB therefore reflects **the conditions under which the PHR was calculated and transmitted**. If path loss, beam, RB allocation, power-control state, or `P_CMAX` has changed since then, the report may no longer represent the current state.

---

## 7. What Does the PHR MAC CE Carry?

The PH field in a MAC CE does not carry a continuous floating-point value. It carries a quantized power-headroom level defined by the specifications.

In Multiple Entry PHR MAC CEs, the `V` field identifies whether PH is based on a real transmission or a reference format:

- `V = 0`: Based on a real transmission
- `V = 1`: Based on a reference format

For Type 1, Type 2, and Type 3 PH in these MAC CEs, `V = 0` also indicates that the octet containing the associated `P_CMAX` field is present, whereas `V = 1` indicates that it is omitted. A scheduler must therefore not assume that every reported `PH` always arrives with a corresponding `P_CMAX`.

Depending on carrier aggregation, dual connectivity, and the reporting configuration, the UE may use a Single Entry or Multiple Entry PHR MAC CE. An implementation should therefore track all of the following:

- Which serving cell does the PH belong to?
- Is it Type 1, Type 2, or Type 3?
- Is it based on a real transmission or a reference format?
- Is the associated `P_CMAX` included?
- When was the report triggered, and when was it transmitted?

---

## 8. What PHR Does Not Tell You

PH is not CQI or SINR.

What PHR tells the gNB is:

> How much margin remains before the UE reaches its maximum power when performing a real or reference uplink transmission according to the power-control equation?

PHR alone does not directly reveal:

- Whether PUSCH will be decoded at the target BLER
- How strong the current interference is
- Which MCS is appropriate
- How much data is actually waiting in the UE's buffer

The scheduler must combine PHR with information such as PUSCH DMRS measurements, HARQ results, OLLA state, and BSR.

---

## 9. Preparing for Scheduler Use

Before using PHR in a scheduler, keep at least these four distinctions in mind:

1. PH is a power margin, not a channel-quality indicator.
2. Real-transmission PH and reference PH cannot be interpreted in exactly the same way.
3. PHR is event- or timer-driven, so it may be stale.
4. The associated `P_CMAX` is not present in every report.

The [next article]({{ '/posts/nr-phr-gnb-scheduling/' | relative_url }}) examines how a gNB uses this information to evaluate candidate RB allocations and combine PHR with SINR, BLER, and BSR when making scheduling decisions.

---

## References

- [3GPP TS 38.213, Physical layer procedures for control — Clause 7.7](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/)
- [3GPP TS 38.321, Medium Access Control protocol specification — Clauses 5.4.6 and 6.1.3](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/)
- [3GPP TS 38.331, Radio Resource Control protocol specification](https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/)
