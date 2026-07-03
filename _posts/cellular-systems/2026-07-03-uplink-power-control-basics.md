---
title: "NR Uplink Power Control (1/3)"
description: "Allocated resource blocks (RBs), power spectral density (PSD), the NR PUSCH power-control equation, and the relationship between P_EMAX and P_CMAX."
date: 2026-07-03
math: true
categories: [Cellular Systems, 5G NR]
tags:
  - 5G NR
  - Uplink Power Control
  - PUSCH
  - Power Budget
  - P_CMAX
---

> **NR Uplink Power Control and PHR Series**
>
> 1. **Power Budget, PSD, and `P_CMAX`**
> 2. What Does a Power Headroom Report Tell the gNB? — Coming soon
> 3. How a gNB Scheduler Uses PHR — Coming soon

To understand the Power Headroom Report (PHR), it helps to first understand how a UE calculates its uplink transmit power.

A common misconception goes like this:

> A UE always has a fixed amount of total transmit power. If fewer RBs are allocated, the same power is spread across fewer RBs, so the power per RB must increase.

This intuition can be correct after the UE has reached its maximum output power, but it does not describe the general behavior of NR uplink power control.

This article starts with four questions:

- How does the cell or BWP bandwidth differ from the number of RBs actually allocated?
- Why does the required PUSCH transmit power increase with the RB allocation?
- What is the difference between `p-Max`, `P_EMAX`, and `P_CMAX`?
- When does reducing the RB allocation actually increase the transmitted PSD?

---

## 1. Linear Power and dBm

Let `p_RB` denote the linear power required per RB and `M_RB` the number of allocated RBs. The total power is then:

$$
p_{\text{total}}
=
p_{\text{RB}} M_{\text{RB}}
$$

When expressed in dBm, multiplication in the linear domain becomes addition:

$$
P_{\text{total}}
=
P_{\text{per-RB}}
+
10\log_{10}(M_{\text{RB}})
$$

Conversely, the power per RB can be derived from the total power as:

$$
P_{\text{per-RB}}
=
P_{\text{total}}
-
10\log_{10}(M_{\text{RB}})
$$

At a constant power density, doubling the number of RBs therefore increases the required total power by approximately 3 dB:

$$
10\log_{10}(2)
\approx
3.01\text{ dB}
$$

---

## 2. Cell Bandwidth vs Allocated RBs

The cell or BWP bandwidth defines the range of frequency resources available to the UE. In contrast, `M_RB` is the number of RBs assigned to a particular PUSCH transmission.

| Concept | Meaning |
|---|---|
| Cell bandwidth | The overall channel bandwidth used by the cell |
| BWP bandwidth | The bandwidth part in which the UE is currently operating |
| Allocated RBs (`M_RB`) | The RBs occupied by the current PUSCH transmission |
| `P_CMAX` | The configured maximum output power applicable under the current conditions |

Rather than assuming that a fixed total power is divided across the entire system bandwidth, it is more useful to view NR uplink power control as establishing a target power density over the allocated bandwidth and then calculating the corresponding total power.

For a simple linear example, suppose the target is 1 mW/RB:

| Allocated RBs | Target per RB | Required total power |
|---:|---:|---:|
| 10 RBs | 1 mW/RB | 10 mW |
| 50 RBs | 1 mW/RB | 50 mW |
| 100 RBs | 1 mW/RB | 100 mW |

As long as the UE can provide the required power, reducing the RB allocation also reduces the total transmit power while the target power per RB remains unchanged.

---

## 3. Intuition Behind the PUSCH Power-Control Equation

With its indices omitted for clarity, the NR PUSCH transmit-power equation has the following simplified structure:

$$
P_{\text{PUSCH}}
=
\min
\left\{
P_{\text{CMAX}},
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

The second argument of `min{}` can be viewed as the power required by the power-control equation for the current PUSCH:

$$
P_{\text{required}}
=
P_O
+
10\log_{10}(2^\mu M_{\text{RB}})
+
\alpha PL
+
\Delta_{TF}
+
f
$$

| Term | Intuitive meaning |
|---|---|
| `P_O` | A gNB-configured, bandwidth-normalized baseline power term |
| `10log10(2^μ M_RB)` | Scaling for numerology and allocated bandwidth |
| `αPL` | Path-loss compensation |
| `Δ_TF` | Transport-format adjustment when the relevant configuration applies |
| `f` | Closed-loop TPC adjustment state |
| `P_CMAX` | The maximum output-power cap used in the calculation |

Care is needed when interpreting `P_O`: it is not simply a fixed transmit-power value for one RB. It is easier to understand as a normalized baseline, or a PSD-like term, used together with the `2^μ M_RB` bandwidth scaling.

If only the number of RBs changes while the numerology and other power-control conditions remain similar, the main change in required power is:

$$
\Delta P_{\text{required}}
\approx
10\log_{10}
\left(
\frac{M_{\text{RB,new}}}{M_{\text{RB,old}}}
\right)
$$

For example, increasing the allocation from 20 RBs to 40 RBs raises the required total power by approximately 3 dB.

---

## 4. `p-Max`, `P_EMAX`, and `P_CMAX`

### 4.1 `p-Max` and `P_EMAX`

The RRC parameter `p-Max` is associated with the maximum UE output power allowed for a cell or carrier. The corresponding quantity in the RF specifications is expressed as `P_EMAX,c`.

For example, even if a UE supports 23 dBm according to its power class, a lower `p-Max` configured by the network can impose a tighter upper limit.

### 4.2 `P_CMAX`

`P_CMAX` is the configured maximum output power that the UE applies to its power-control calculation for a particular carrier and transmission condition.

It can be affected by factors such as:

- UE power class
- `P_EMAX`
- MPR and A-MPR
- P-MPR
- Operating band and channel bandwidth
- Modulation and waveform conditions
- Carrier aggregation, dual connectivity, and simultaneous transmissions
- MPE or other power-management backoffs

Consequently, `P_CMAX` can equal `P_EMAX`, but the two are not always identical. `P_CMAX` may also change as the transmission conditions change.

The distinction can be summarized as follows:

> `P_EMAX` represents an upper limit associated with the maximum power allowed by the network, whereas  
> `P_CMAX` is the effective maximum output power used by the UE under the current power-control conditions.

---

## 5. When the UE Is Not Power-Limited

If the UE can provide the power required by the power-control equation:

$$
P_{\text{actual,total}}
=
P_{\text{required,total}}
<
P_{\text{CMAX}}
$$

Reducing the RB allocation lowers the required and actual total power, while the target PSD remains essentially unchanged.

| RBs | Required total | Actual total | Actual per RB |
|---:|---:|---:|---:|
| 10 RBs | 10 mW | 10 mW | 1 mW/RB |
| 50 RBs | 50 mW | 50 mW | 1 mW/RB |

The more accurate statement is therefore:

> When the UE is not power-limited, reducing the RB allocation does not automatically increase the actual PSD.

---

## 6. When the UE Is Power-Limited

If the required power exceeds `P_CMAX`, the actual total transmit power is capped:

$$
P_{\text{required,total}}
>
P_{\text{CMAX}}
$$

$$
P_{\text{actual,total}}
\approx
P_{\text{CMAX}}
$$

Suppose that the target is 1 mW/RB, `P_CMAX = 50 mW`, and the gNB allocates 100 RBs:

| RBs | Required total | Actual total | Actual per RB |
|---:|---:|---:|---:|
| 100 RBs | 100 mW | 50 mW | 0.5 mW/RB |
| 50 RBs | 50 mW | 50 mW | 1 mW/RB |

With 100 RBs, the UE reaches its maximum output power and cannot maintain the target PSD. Reducing the allocation to 50 RBs brings the required total power back within the UE's power budget, allowing the actual PSD to recover to the target level.

The statement “reducing the RB allocation increases the PSD” therefore requires an important condition:

> When a UE is already power-limited, reducing the RB allocation can restore its actual PSD.

---

## 7. Connecting This to PHR

The key ideas so far can be summarized by two equations:

$$
P_{\text{required}}
\approx
P_O
+
10\log_{10}(2^\mu M_{\text{RB}})
+
\alpha PL
+
\Delta_{TF}
+
f
$$

$$
P_{\text{actual}}
=
\min
\{
P_{\text{CMAX}},
P_{\text{required}}
\}
$$

How, then, can the gNB determine how close the UE is to `P_CMAX`?

That information is provided by the Power Headroom Report, which will be the subject of the next article in this series.

---

## References

- [3GPP TS 38.213, Physical layer procedures for control](https://www.etsi.org/deliver/etsi_ts/138200_138299/138213/)
- [3GPP TS 38.101-1, UE radio transmission and reception; Range 1 standalone](https://www.etsi.org/deliver/etsi_ts/138100_138199/13810101/)
- [3GPP TS 38.101-2, UE radio transmission and reception; Range 2 standalone](https://www.etsi.org/deliver/etsi_ts/138100_138199/13810102/)
