

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