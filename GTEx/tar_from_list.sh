tar_from_list_pigz() {
       tissue="$1"; wf="$2"
       echo "Archiving $tissue ($wf)..."
       gsutil cat "gs://$BUCKET/archives/$tissue/$wf.beds.txt" \
         | sed 's#^gs://[^/]*/##' | grep -v '^[[:space:]]*$' \
        | tar -C "$MNT" -cf - -T - \
        | pigz -9 \
        | gsutil -o "GSUtil:parallel_composite_upload_threshold=150M" cp - \
            "gs://$BUCKET/archives/$tissue/${tissue}-${wf}.beds.tgz"
}

declare -A TWF=(
      [Stomach]=381f7e59-f0a3-4197-90e6-b9c523a6e7d3
      [Adrenal_Gland]=03be0ad4-15c4-41ac-a26c-893cf09fa04b
      [Brain]=574078bc-6bde-4f68-ba1a-ddc3a3d132b0
      [Skin]=1381bb55-c517-4d11-afb1-0e134204c2c3
      [Blood_Vessel]=a6211646-9131-414f-ac72-fffd43e641d0
      [Esophagus]=26715c1d-e685-4dfb-b17d-a791ac044ffc
      [Adipose_Tissue]=e52db0ca-1ee0-488a-9576-a259367ca149
    )

tar_all_except_colon() {
      local max_jobs=3 n=0
      for tissue in "${!TWF[@]}"; do
        wf="${TWF[$tissue]}"
        tar_from_list_pigz "$tissue" "$wf" &
        n=$((n+1))
        if (( n % max_jobs == 0 )); then wait; fi
      done
      wait
}