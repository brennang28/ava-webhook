# WSL2 Persistence Tracker

- [x] **Phase 1: Research & Planning**
    - [x] Analyze `journalctl` for shutdown root cause (Confirmed: Sleep at 9:27 AM, not reboot)
    - [x] Verify `cron` service status
    - [x] Create Implementation Plan
- [x] **Phase 2: Windows Side Configuration (User Verified)**
    - [x] Add `vmIdleTimeout=-1` to `.wslconfig`
    - [x] Create Windows Task Scheduler "Kickstart" task
    - [x] Disable Windows Sleep in Power Settings
- [x] **Phase 3: Linux Side Hardening**
    - [x] Replace `cron` with `systemd` user timers (Persistent=true)
    - [x] Robustify `watcher.py` and `generator.py` for varying schemas
    - [x] Test persistence by disconnecting SSH
- [ ] **Phase 4: Verification**
    - [ ] Verify 6 AM execution tomorrow morning
    - [x] Initial Manual Recovery (20 jobs currently processing)
    - [ ] Final Walkthrough
