## v3.0.0 (2025-02-01)

### Production Release

### New
- f735197 TMS : Report Overtime Attendances (Request vs Realization)
- 2bf0f6c PAM : Menambahkan fields employment details di personal admin
- b9a517e TMS : Report PDF dan Excel Overtime Request 2
- 8e9538e TMS : Mengubah susunan field pada form TMS Entry Summary
- 5c4a113 TMS : Menukar posisi field Rel Time dengan App Time di OT Attendances
- 3c914b3 TMS : Menambahkan field OT, OT Flat, dan Night Shift pada header TMS Entry Summary

### Improvement
- 11113c5 TMS : Mengubah susunan field pada form Permission Entry
- 8f6138f TMS : Mengubah susunan field pada form Overtime Request
- d070a11 TMS : Mengubah susunan field pada form Adjustment Request

### Fix
- 05ae2aa TMS : Fix field Sub Department yang terfilter karena Area & BU readonly di Overtime Request

---
### Main branch - Development 

### Improvement
- 23576d6 PAM: Link tabel Employment Details dengan tabel Product
- 1b966ec PAM : Menambah field Employment Status untuk Mutasi dengan Service Type ACTV
- 3b9c27c TMS: Menambah State Cancel by System di form Permission Entry


## v2.0.0 (2025-01-25)

### Production Release

### Fix
- b1e48e0 [TMS] Fix button Mass Approve HRD, Mass Approve CA dan Mass Approve TMS Summary
- a854d8e [PAM] NIK ke replace dengan yang terbaru ketika ada transaksi di Mutation

---

### Main branch - Development 

### New
- eb62df9 [TMS] adding new feature leave allocation
- 09326d1 [TMS] Menambahkan field OT, OT Flat, dan Night Shift pada header TMS Entry Summary

### Improvement
- d6758ec [TMS] Mengubah susunan field pada form Adjustment Request
- 28f3d44 [TMS] Mengubah susunan field pada form Overtime Request
- 88ec98f [TMS] Mengubah susunan field pada form TMS Entry Summary
- 3d4f04e [TMS] Menukar posisi field Rel Time dengan App Time di OT Attendances

### Fix
-  6eb1f10 [TMS] Fix button Mass Approve HRD, Mass Approve CA dan Mass Approve TMS Summary

## v1.0.0 (2025-01-18)

### Production Release

### New
- 72a72ae [PAM] Penambahan field Employment Status ketika Service Type = CORR di Employee Mutation

### Bug fixes
- 7176a623 [TMS] Perbaiki OT Holiday yang masuk tanpa approval
- 7176a623 [PAM] Field Workingday Menghilang
- 41045dd0 [PAM] Issue kurang library '_'
- 4e2660b6 [TMS] Tambah field employee_id di Absen Staging
- 5c2cdd3  [PAM] Fix Group Button Close
- f7d2f83  [PAM] fix field WD di benefit/allowance
- 99508297 [PAM] Menambahkan field flag OT Flat
- b06f47e1 [TMS] Perbaiki hitungan Approval TMS Entry Summary di Tree setelah Proses ulang
- e5e50191 [PAM] Employment Status disesuaikan berdasarkan Job Status
- 9882c7a8 [PAM] fix kondisi readonly field emp_status state == approved
- 6730d846 [TMS] Menghilangkan widget timepicker pada field datetime
- 6730d846 [TMS] Mengubah field employee_id di TMSEntry Detail
  
---

### Main branch - Development 

### New
- 7c37066 [PAM] Penambahan field Tanggal diterima & Tanggal dikembalikan

### Fix
- c1a6a04 [PAM] NIK ke replace dengan yang terbaru ketika ada transaksi di Mutation
- 966c2d3 [TMS] Tambah field employee_id di Absen Staging
- 61b43c5 [TMS] Perbaiki OT Holiday yang masuk tanpa approval
- 4f0481f [TMS] fix widget pada field time
- f4d3b06 [PAM] Update 'Employment Status' dan 'Employment Tracking' berdasarkan transaksi Employee Exit
- 7c37066 [PAM] Location berdasarkan Business Unit