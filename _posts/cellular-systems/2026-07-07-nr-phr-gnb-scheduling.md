---
title: "NR Power Headroom Report (3/3): How a gNB Scheduler Uses PHR"
description: "How a gNB uses PHR to estimate RB feasibility, separate power limits from link quality, and choose RB × MCS candidates."
date: 2026-07-07
math: true
categories: [Cellular Systems, 5G NR]
tags:
  - 5G NR
  - PHR
  - Scheduler
  - RB Allocation
  - MCS
  - PUSCH
---

> **NR Uplink Power Control and PHR Series**
>
> 1. [Power Budget, PSD, and `P_CMAX`]({{ '/posts/uplink-power-control-basics/' | relative_url }})
> 2. [What Does a Power Headroom Report Tell the gNB?]({{ '/posts/nr-powerheadroom-report/' | relative_url }})
> 3. **How a gNB Scheduler Uses PHR**

In the previous two articles, we looked at [NR uplink power budgeting]({{ '/posts/uplink-power-control-basics/' | relative_url }}) and [what a Power Headroom Report tells the gNB]({{ '/posts/nr-powerheadroom-report/' | relative_url }}).

Now we can return to the scheduler-side question:

> If a UE has low PH, should the gNB reduce the RB allocation or lower the MCS?

The short answer is: **PHR alone cannot decide that**.

PHR is closer to a constraint on whether a candidate grant fits inside the UE's power budget. MCS is mainly selected from link-quality information such as SINR, HARQ feedback, and BLER. The RB allocation should be chosen by looking at both buffer demand and the UE's power budget.

---

## 1. What the Scheduler Looks at Together

When a gNB makes an uplink scheduling decision, PHR is only one of several inputs.

| Input | Question it helps answer |
|---|---|
| PH and associated `P_CMAX` | Does the UE still have transmit-power margin? |
| Actual/reference basis | How directly can this PH be mapped to a concrete grant? |
| Previous PUSCH grant | Under which RB, MCS, and numerology conditions was this PH produced? |
| BSR | How much uplink data does the UE need to send? |
| PUSCH DMRS SINR | What is the current uplink link quality? |
| HARQ ACK/NACK, BLER, OLLA | Is the selected MCS meeting the target reliability? |
| TPC and beam state | Has the power-control or spatial condition changed? |

So the role of PHR can be summarized like this:

> PHR answers “Can the UE transmit this PUSCH bandwidth at the target power?” more directly than “Can this MCS be decoded?”

---

## 2. First Check the Scope of the Report

Before applying a PH value to a candidate grant, the scheduler has to check the report context.

1. Is this Type 1 PH?
2. Is it based on an actual PUSCH transmission or a reference format?
3. Which serving cell and UL carrier does it describe?
4. Have path loss, beam, or TPC state changed since the report was calculated?
5. Is the associated `P_CMAX` included?

Type 1 PH based on an actual PUSCH is a useful starting point because it can be tied to a concrete allocation.

Reference-format PH is different. It was not calculated from an actual RB allocation and transport format, so it should not be treated as the current grant's remaining margin. The scheduler needs to translate it through the configured reference condition before comparing it with a candidate grant.

---

## 3. Translating Reported PH to a Candidate RB Allocation

Assume, for a moment, that numerology, path loss, power-control state, `P_CMAX`, and transport-format effects do not change much. Then the required power change caused by changing the number of RBs can be approximated as:

$$
\Delta P_{\text{RB}}
\approx
10\log_{10}
\left(
\frac{M_{\text{RB,new}}}{M_{\text{RB,reported}}}
\right)
$$

That gives a useful intuition for the candidate grant:

$$
PH_{\text{predicted}}
\approx
PH_{\text{reported}}
-
10\log_{10}
\left(
\frac{M_{\text{RB,new}}}{M_{\text{RB,reported}}}
\right)
-
\Delta\Delta_{\text{TF}}
$$

Here, `ΔΔ_TF` represents the difference in transport-format correction between the reported condition and the candidate condition, when that correction is configured and applicable.

This is not a scheduler algorithm specified by 3GPP. It is a practical approximation for moving from a reported condition to a candidate grant.

In a real scheduler, the following can also change:

- `P_CMAX`
- Path-loss reference or beam condition
- TPC adjustment state
- Simultaneous UL transmission and power sharing
- Transform precoding and waveform condition

---

## 4. Worked Example: PH Was 6 dB at 20 RB

Assume the UE transmitted an actual PUSCH on 20 RB, and the Type 1 PH was 6 dB.

If all other conditions stay the same, increasing the grant to 40 RB adds about 3 dB of required power:

$$
10\log_{10}
\left(
\frac{40}{20}
\right)
\approx
3\text{ dB}
$$

The predicted PH becomes about 3 dB:

$$
PH_{\text{predicted}}
\approx
6 - 3
=
3\text{ dB}
$$

Increasing the grant to 80 RB adds about 6 dB:

$$
10\log_{10}
\left(
\frac{80}{20}
\right)
\approx
6\text{ dB}
$$

The predicted PH becomes about 0 dB.

| Candidate RB | Extra power needed for RB scaling | Predicted PH |
|---:|---:|---:|
| 20 RB | 0 dB | 6 dB |
| 40 RB | about 3 dB | about 3 dB |
| 80 RB | about 6 dB | about 0 dB |

This calculation does not mean that 80 RB is always optimal. Because of PHR quantization, report age, `P_CMAX`, MCS/`Δ_TF`, path loss, and implementation margin, a scheduler may avoid landing exactly at 0 dB.

---

## 5. Why RB Allocation Matters for a Power-Limited UE

If the UE is not power-limited, reducing the RB allocation usually reduces both the required total power and the actual total power, while the target PSD is mostly maintained.

$$
P_{\text{actual}}
=
P_{\text{required}}
<
P_{\text{CMAX}}
$$

Once the UE reaches `P_CMAX`, however, total transmit power is capped. With a wider allocation, the actual PSD across the allocated bandwidth can fall below the target PSD.

$$
P_{\text{actual}}
\approx
P_{\text{CMAX}}
<
P_{\text{required}}
$$

In that case, reducing RBs directly reduces the required total power and can help the remaining RBs recover toward the target PSD.

So when PH is negative or very low, the most direct power-budget lever available to the scheduler is usually the RB allocation.

---

## 6. RB Reduction and MCS Lowering Do Different Jobs

| Action | What it directly changes | Main purpose |
|---|---|---|
| RB reduction | `10log10(M_RB)` | Reduce required total power and allocated bandwidth |
| MCS lowering | Coding/modulation robustness | Lower the required SINR and improve BLER |
| TPC adjustment | Closed-loop power-control state | Adjust the received-power target |
| UL beam change | Effective path loss | Improve coverage or spatial condition |
| UL carrier/CG adjustment | Simultaneous power sharing | Relax the power budget per serving cell |

Lowering MCS does not always directly reduce UE transmit power.

- If `Δ_TF` is configured and applicable, the transport format can affect the power-control equation.
- However, the primary role of MCS lowering is to reduce the required SINR and improve decoding robustness.
- Sending the same payload with a lower MCS may require more RBs or more symbols, which can increase the bandwidth-side power requirement.

Therefore, the scheduler should not treat RB and MCS as two independent single-purpose knobs. It should choose an **RB × MCS combination** that satisfies TBS, link reliability, and power-budget constraints together.

---

## 7. Typical PH and Link-Quality Scenarios

| PH | SINR/BLER | Interpretation | Possible direction |
|---|---|---|---|
| Low | Good | The link is decodable, but power margin is small | Keep MCS if link quality supports it; limit RB expansion |
| Low or negative | Poor | The UE may be power-limited and short on PSD | Reduce RBs; if needed, lower MCS and check beam/TPC |
| Sufficient | Poor | Maximum-power shortage may not be the main cause | Check MCS, interference, channel estimation, and beam |
| Sufficient | Good | Both power margin and link margin exist | Increase RBs if BSR is sufficient; raise MCS if link adaptation supports it |

Even here, sufficient PH by itself is not a reason to raise MCS. MCS decisions are primarily driven by SINR, HARQ feedback, target BLER, and OLLA.

---

## 8. Reading PH Together with `P_CMAX`

If an actual-transmission report includes the associated `P_CMAX`, the scheduler can estimate the required transmit power:

$$
P_{\text{required}}
\approx
P_{\text{CMAX}}
-
PH
$$

For example:

- If `P_CMAX = 23 dBm` and `PH = 3 dB`, the estimated required power is about 20 dBm.
- If `P_CMAX = 20 dBm` and `PH = 3 dB`, the estimated required power is about 17 dBm.

The same PH can therefore represent different underlying power conditions when `P_CMAX` differs.

This also means that time-series comparisons need context. The associated `P_CMAX` may be absent in some reference-format cases, and `P_CMAX` itself can change because of MPR, power management, band combination, or simultaneous-transmission conditions.

---

## 9. A Conceptual Scheduler Flow

Implementation algorithms differ by vendor, but the conceptual flow is often close to this:

```text
1. Check PHR context
   - Serving cell, PH type, actual/reference basis, report age

2. Evaluate power feasibility of a candidate grant
   - RB scaling, P_CMAX, TPC, beam/path-loss condition

3. Check buffer demand
   - BSR, QoS, latency, available UL resources

4. Run link adaptation
   - SINR, HARQ/BLER, and OLLA determine MCS candidates

5. Select an RB × MCS combination
   - Choose a candidate that satisfies both TBS and power margin
```

PHR is not a hard scheduling command in this process. It is an input that constrains or evaluates candidate grants.

---

## 10. Limits of PHR-Based Decisions

When using PHR in a scheduler, keep these limits in mind:

- PH is quantized.
- PHR is not reported every slot, so it can be stale.
- Reference PH is not the margin of an actual grant.
- The associated `P_CMAX` is not always included.
- Path loss, TPC, beam, and simultaneous-transmission conditions can change.
- PH does not indicate SINR, interference, or BLER by itself.
- 3GPP defines PHR calculation and reporting, but it does not define a vendor scheduler algorithm.

A practical scheduler therefore applies implementation margin to PH and combines it with recent PUSCH measurements and HARQ history.

---

## 11. Summary

From the gNB scheduler's point of view, the key points are:

1. PH is UE transmit-power margin, not channel quality.
2. Type 1 PH based on an actual PUSCH is a useful starting point for extrapolating from the reported PUSCH to a candidate RB allocation.
3. Reference PH should not be used directly as the margin of an actual allocation.
4. RB reduction directly reduces the required total transmit power.
5. MCS lowering mainly improves decoding robustness; it does not always lower transmit power.
6. The scheduler has to combine PHR, `P_CMAX`, BSR, SINR, HARQ/BLER, and grant history.

In the end, the scheduler's problem is not simply “PH is low, so reduce RBs.”

> The point of using PHR is to find an RB × MCS combination that satisfies UE power budget, link quality, and buffer demand together.

---

## References

- [3GPP TS 38.213, Physical layer procedures for control — PUSCH power control and PHR](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/)
- [3GPP TS 38.321, Medium Access Control protocol specification — Power Headroom Reporting](https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/)
- [3GPP TS 38.214, Physical layer procedures for data — PUSCH and link adaptation](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/)
