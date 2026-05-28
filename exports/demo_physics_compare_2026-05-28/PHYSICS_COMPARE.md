# Physics comparison

Generated: 2026-05-28T14:28:03.809533+00:00

## Safest candidate summary

- Case A safest candidate: `direct_drive-ddm-50`
- Case B safest candidate: `direct_drive-ddm-50`
- Safety ranking prioritizes physics pass status, then fewer physics warnings, then the worst conservative category margin.
- `direct_drive-ddm-50` is safest for Case A (baseline) because it ranks highest after physics pass status, warning count, and worst category margin; conservative category margins are structural=0.3585, drivetrain=0.18, thermal=0.3725, controls/tracking=0.3.
- `direct_drive-ddm-50` is safest for Case B (constrained) because it ranks highest after physics pass status, warning count, and worst category margin; conservative category margins are structural=0.3585, drivetrain=0.18, thermal=0.3725, controls/tracking=0.3.
- Belt-axis candidates are less safe in this run because their drivetrain and thermal checks carry high-severity risk flags, while the direct-drive candidate passes all four check groups.

## Per-candidate physics margins

### Case A (baseline)
| Candidate | Physics summary | Passed | Key margins |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | True | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>thermal_margin=0.3725<br>structural_safety_factor_proxy=5.0607 |
| belt_axis-M2-D2-T3 | fail | False | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=-0.026<br>structural_safety_factor_proxy=4.7255 |
| belt_axis-M2-D3-T3 | fail | False | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=-0.026<br>structural_safety_factor_proxy=4.6036 |

### Case B (constrained)
| Candidate | Physics summary | Passed | Key margins |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | True | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>thermal_margin=0.3725<br>structural_safety_factor_proxy=5.0607 |
| belt_axis-M2-D2-T3 | fail | False | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=-0.026<br>structural_safety_factor_proxy=4.7255 |
| belt_axis-M2-D3-T3 | fail | False | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=-0.026<br>structural_safety_factor_proxy=4.6036 |

## structural

### Case A (baseline)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | estimated_max_deflection_mm=0.3207<br>structural_deflection_margin=0.3585<br>estimated_stress_proxy_mpa=23.7122<br>structural_stress_margin=0.8024<br>structural_safety_factor_proxy=5.0607 | — |
| belt_axis-M2-D2-T3 | pass | estimated_max_deflection_mm=0.3435<br>structural_deflection_margin=0.313<br>estimated_stress_proxy_mpa=25.3939<br>structural_stress_margin=0.7884<br>structural_safety_factor_proxy=4.7255 | — |
| belt_axis-M2-D3-T3 | pass | estimated_max_deflection_mm=0.3526<br>structural_deflection_margin=0.2948<br>estimated_stress_proxy_mpa=26.0666<br>structural_stress_margin=0.7828<br>structural_safety_factor_proxy=4.6036 | — |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | estimated_max_deflection_mm=0.3207<br>structural_deflection_margin=0.3585<br>estimated_stress_proxy_mpa=23.7122<br>structural_stress_margin=0.8024<br>structural_safety_factor_proxy=5.0607 | — |
| belt_axis-M2-D2-T3 | pass | estimated_max_deflection_mm=0.3435<br>structural_deflection_margin=0.313<br>estimated_stress_proxy_mpa=25.3939<br>structural_stress_margin=0.7884<br>structural_safety_factor_proxy=4.7255 | — |
| belt_axis-M2-D3-T3 | pass | estimated_max_deflection_mm=0.3526<br>structural_deflection_margin=0.2948<br>estimated_stress_proxy_mpa=26.0666<br>structural_stress_margin=0.7828<br>structural_safety_factor_proxy=4.6036 | — |

## thermal

### Case A (baseline)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | estimated_temp_rise_c=8.8291<br>thermal_margin=0.3725<br>duty_weighted_load=0.6275 | — |
| belt_axis-M2-D2-T3 | fail | estimated_temp_rise_c=16.1108<br>thermal_margin=-0.026<br>duty_weighted_load=1.026 | risk_thermal_margin_low |
| belt_axis-M2-D3-T3 | fail | estimated_temp_rise_c=16.1108<br>thermal_margin=-0.026<br>duty_weighted_load=1.026 | risk_thermal_margin_low |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | estimated_temp_rise_c=8.8291<br>thermal_margin=0.3725<br>duty_weighted_load=0.6275 | — |
| belt_axis-M2-D2-T3 | fail | estimated_temp_rise_c=16.1108<br>thermal_margin=-0.026<br>duty_weighted_load=1.026 | risk_thermal_margin_low |
| belt_axis-M2-D3-T3 | fail | estimated_temp_rise_c=16.1108<br>thermal_margin=-0.026<br>duty_weighted_load=1.026 | risk_thermal_margin_low |

## drivetrain

### Case A (baseline)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>efficiency_margin=0.18<br>direct_drive_speed_margin=4.0<br>direct_drive_torque_margin=0.9792<br>direct_drive_duty_weighted_margin=2.0475 | — |
| belt_axis-M2-D2-T3 | fail | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>efficiency_margin=0.086<br>belt_stretch_margin=-1.943<br>belt_reflected_inertia_margin=0.325<br>belt_required_speed_mps=0.6 | risk_belt_stretch_margin_low |
| belt_axis-M2-D3-T3 | fail | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>efficiency_margin=0.0948<br>belt_stretch_margin=-1.943<br>belt_reflected_inertia_margin=0.325<br>belt_required_speed_mps=0.6 | risk_belt_stretch_margin_low |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>efficiency_margin=0.18<br>direct_drive_speed_margin=4.0<br>direct_drive_torque_margin=0.9792<br>direct_drive_duty_weighted_margin=2.0475 | — |
| belt_axis-M2-D2-T3 | fail | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>efficiency_margin=0.086<br>belt_stretch_margin=-1.943<br>belt_reflected_inertia_margin=0.325<br>belt_required_speed_mps=0.6 | risk_belt_stretch_margin_low |
| belt_axis-M2-D3-T3 | fail | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>efficiency_margin=0.0948<br>belt_stretch_margin=-1.943<br>belt_reflected_inertia_margin=0.325<br>belt_required_speed_mps=0.6 | risk_belt_stretch_margin_low |

## controls

### Case A (baseline)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | controls_motion_profile_margin=0.8<br>controls_torque_speed_margin=0.8<br>controls_duty_margin=0.3<br>speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>duty_weighted_load=0.6275 | — |
| belt_axis-M2-D2-T3 | pass | controls_motion_profile_margin=0.2<br>controls_torque_speed_margin=0.2<br>controls_duty_margin=0.3<br>speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=1.026 | — |
| belt_axis-M2-D3-T3 | pass | controls_motion_profile_margin=0.2<br>controls_torque_speed_margin=0.2<br>controls_duty_margin=0.3<br>speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=1.026 | — |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | controls_motion_profile_margin=0.8<br>controls_torque_speed_margin=0.8<br>controls_duty_margin=0.3<br>speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>duty_weighted_load=0.6275 | — |
| belt_axis-M2-D2-T3 | pass | controls_motion_profile_margin=0.2<br>controls_torque_speed_margin=0.2<br>controls_duty_margin=0.3<br>speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=1.026 | — |
| belt_axis-M2-D3-T3 | pass | controls_motion_profile_margin=0.2<br>controls_torque_speed_margin=0.2<br>controls_duty_margin=0.3<br>speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=1.026 | — |

## Delta summary across cases

- Topology changed: `False`
- Top candidate changed: `False`
- Top score delta (B - A): `0.0`
- Physics pass count delta (B - A): `0`
- Physics warning count delta (B - A): `0`
- Risk flags added in B: `[]`
- Risk flags removed in B: `[]`

| Candidate | Score delta | Summary changed | Pass changed |
| --- | --- | --- | --- |
| belt_axis-M2-D2-T3 | 0.0 | False | False |
| belt_axis-M2-D3-T3 | 0.0 | False | False |
| direct_drive-ddm-50 | 0.0 | False | False |

## Category margin deltas (Case B - Case A)

| Candidate | Structural | Drivetrain | Thermal | Controls/tracking |
| --- | --- | --- | --- | --- |
| belt_axis-M2-D2-T3 | 0.0 | 0.0 | 0.0 | 0.0 |
| belt_axis-M2-D3-T3 | 0.0 | 0.0 | 0.0 | 0.0 |
| direct_drive-ddm-50 | 0.0 | 0.0 | 0.0 | 0.0 |
