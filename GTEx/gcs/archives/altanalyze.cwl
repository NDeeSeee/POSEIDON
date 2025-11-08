version 1.0

task BedToJunction {
    input {
        Array[File] bed_files
        Int cpu_cores = 1
        String species = "Hs"
        String memory = "8 GB"
        String disk_type = "HDD"
        Int preemptible = 1
        Int max_retries = 1
        Boolean counts_only = true
        String docker_image = "ndeeseee/altanalyze:v1.6.39"
        Float disk_multiplier = 1.3
        Int disk_buffer_gb = 10
        Int min_disk_gb = 50
    }

    Int bed_gib = ceil(size(bed_files, "GiB"))
    Int bed_disk_candidate = ceil(bed_gib * disk_multiplier + disk_buffer_gb)
    Int disk_space = if bed_disk_candidate > min_disk_gb then bed_disk_candidate else min_disk_gb

    command <<<
        set -euo pipefail
        # Optional inline monitoring: start monitor.sh if present (no-op otherwise)
        MON_START() {
            if [[ "${ENABLE_MONITORING:-1}" != "0" ]]; then
                # Avoid starting a second monitor if one is already running (e.g., workspace-level monitoring)
                # Prefer a quick file-based guard first (workspace monitor usually writes this immediately)
                if [[ -s /cromwell_root/monitoring/metadata.json ]]; then return 0; fi
                if pgrep -f "monitor.sh" >/dev/null 2>&1; then return 0; fi
                if command -v monitor.sh >/dev/null 2>&1; then
                    MON_DIR="$PWD/monitoring" MON_MAX_SAMPLES=0 nohup monitor.sh >/dev/null 2>&1 & echo $! > .mon.pid || true
                elif [[ -x /usr/local/bin/monitor.sh ]]; then
                    MON_DIR="$PWD/monitoring" MON_MAX_SAMPLES=0 nohup /usr/local/bin/monitor.sh >/dev/null 2>&1 & echo $! > .mon.pid || true
                fi
            fi
        }
        MON_STOP() { if [[ -f .mon.pid ]]; then kill "$(cat .mon.pid)" >/dev/null 2>&1 || true; fi }
        trap MON_STOP EXIT
        MON_START
        mkdir -p bed
        mkdir -p altanalyze_output/ExpressionInput

        if [ ${#BED_FILES[@]} -eq 0 ]; then
            echo "No BED files found for junction analysis" >&2
            exit 1
        fi
        # Copy inputs into a local folder with a permission-friendly fallback
        copy_one() {
            local src="$1"
            local bn
            bn=$(basename "$src")
            # Try a straight copy first; if that fails due to perms, relax perms and retry; as last resort, stream-copy
            cp -f "$src" "bed/$bn" 2>/dev/null || {
                chmod a+r "$src" 2>/dev/null || true
                cp -f "$src" "bed/$bn" 2>/dev/null || cat "$src" > "bed/$bn"
            }
        }
        for bed in "${BED_FILES[@]}"; do
            copy_one "$bed"
        done

        # Some legacy AltAnalyze utilities expect /mnt/altanalyze_output; provide a symlink to our working output
        ln -s "$PWD/altanalyze_output" /mnt/altanalyze_output 2>/dev/null || true

        # Run AltAnalyze junction step
        if [ "~{counts_only}" = "true" ]; then
            PERFORM_ALT=no SKIP_PRUNE=yes /usr/src/app/AltAnalyze.sh bed_to_junction "bed"
        else
            PERFORM_ALT=yes SKIP_PRUNE=no /usr/src/app/AltAnalyze.sh bed_to_junction "bed"
        fi

        # Ensure expected event file exists to keep downstream consumers happy
        EVENT_FILE="altanalyze_output/AltResults/AlternativeOutput/~{species}_RNASeq_top_alt_junctions-PSI_EventAnnotation.txt"
        if [ ! -s "$EVENT_FILE" ]; then
            mkdir -p "$(dirname "$EVENT_FILE")"
            printf "UID\n" > "$EVENT_FILE"
        fi

        # Collect outputs
        tar -czf altanalyze_output.tar.gz altanalyze_output
    >>>

    output {
        File results_archive = "altanalyze_output.tar.gz"
    }

    runtime {
        docker: docker_image
        cpu: cpu_cores
        memory: memory
        disks: "local-disk ~{disk_space} ~{disk_type}"
        preemptible: preemptible
        maxRetries: max_retries
    }
}
