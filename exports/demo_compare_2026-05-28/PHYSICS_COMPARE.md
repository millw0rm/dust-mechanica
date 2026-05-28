# Physics comparison

Generated: 2026-05-28T13:38:26.685395+00:00

## Per-candidate physics margins

### Case A (baseline)
| Candidate | Physics summary | Passed | Key margins |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | True | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>thermal_margin=0.6463<br>structural_safety_factor_proxy=5.0607 |
| belt_axis-M2-D2-T3 | pass_with_warnings | True | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=0.4506<br>structural_safety_factor_proxy=4.7255 |
| belt_axis-M2-D3-T3 | pass_with_warnings | True | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=0.4506<br>structural_safety_factor_proxy=4.6036 |

### Case B (constrained)
| Candidate | Physics summary | Passed | Key margins |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | True | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>thermal_margin=0.6463<br>structural_safety_factor_proxy=5.0607 |
| belt_axis-M2-D2-T3 | pass_with_warnings | True | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=0.4506<br>structural_safety_factor_proxy=4.7255 |
| belt_axis-M2-D3-T3 | pass_with_warnings | True | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>thermal_margin=0.4506<br>structural_safety_factor_proxy=4.6036 |

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
| direct_drive-ddm-50 | pass | estimated_temp_rise_c=0.27<br>thermal_margin=0.6463<br>duty_weighted_load=0.3537 | — |
| belt_axis-M2-D2-T3 | pass | estimated_temp_rise_c=39.1895<br>thermal_margin=0.4506<br>duty_weighted_load=0.5494 | — |
| belt_axis-M2-D3-T3 | pass | estimated_temp_rise_c=39.1895<br>thermal_margin=0.4506<br>duty_weighted_load=0.5494 | — |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | estimated_temp_rise_c=0.27<br>thermal_margin=0.6463<br>duty_weighted_load=0.3537 | — |
| belt_axis-M2-D2-T3 | pass | estimated_temp_rise_c=39.1895<br>thermal_margin=0.4506<br>duty_weighted_load=0.5494 | — |
| belt_axis-M2-D3-T3 | pass | estimated_temp_rise_c=39.1895<br>thermal_margin=0.4506<br>duty_weighted_load=0.5494 | — |

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
| direct_drive-ddm-50 | pass | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>duty_weighted_load=0.3537 | — |
| belt_axis-M2-D2-T3 | pass | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=0.5494 | — |
| belt_axis-M2-D3-T3 | pass | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=0.5494 | — |

### Case B (constrained)
| Candidate | Status | Margins | Warnings |
| --- | --- | --- | --- |
| direct_drive-ddm-50 | pass | speed_headroom_ratio=4.0<br>torque_margin=0.9792<br>duty_weighted_load=0.3537 | — |
| belt_axis-M2-D2-T3 | pass | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=0.5494 | — |
| belt_axis-M2-D3-T3 | pass | speed_headroom_ratio=0.25<br>torque_margin=0.2742<br>duty_weighted_load=0.5494 | — |

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
