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