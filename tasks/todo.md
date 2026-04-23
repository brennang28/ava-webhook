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
    - [x] Fix systemd unit paths and PYTHONPATH for module execution
    - [x] Robustify `watcher.py` and `generator.py` for varying schemas
    - [x] Test persistence by disconnecting SSH
- [ ] **Phase 4: Verification**
    - [ ] Verify 6 AM execution tomorrow morning
    - [x] Initial Manual Recovery (20 jobs currently processing)
    - [ ] Final Walkthrough

## Document Formatting Task (April 22)
- [x] **Phase 1: High-Fidelity Infrastructure**
    - [x] Integrate `python-docx` for binary document handling
    - [x] Update `AvaGenerator` to load `.docx` templates instead of `.txt`
    - [x] Implement `_write_to_template` with placeholder replacement and style preservation
- [x] **Phase 2: Integration & Deployment**
    - [x] Update Drive upload logic for `MediaInMemoryUpload` with `.docx` MIME type
    - [x] Clean up legacy `.txt` assets
- [x] **Phase 3: Verification**
    - [x] Verified binary buffer generation and content injection via standalone test
    - [x] Confirmed file size and structure preservation (CL ~7.8K, Resume ~378K)
