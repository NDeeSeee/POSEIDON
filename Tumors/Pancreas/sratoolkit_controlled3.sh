INPUTFILE=$1
SAMPLE=$(basename $INPUTFILE .sra) #removes the .txt from the file name only (parent folder name)
DIR=$(pwd)


cat <<EOF
#BSUB -L /bin/bash
#BSUB -W 150:00
#BSUB -n 4
#BSUB -R "span[ptile=4]"
#BSUB -M 10000
#BSUB -e $DIR/logs/%J_sra.err.txt
#BSUB -o $DIR/logs/%J_sra.out.txt
#BSUB -J sra_download

cd $DIR

mkdir -p logs

module load sratoolkit/3.1.1
module load aspera/3.9.1 

#Bioproject PRJNA1093555. Controlled Pancreatic Samples
#generating a cart file will all samples was impossible for some reason. Thus, I've resorted to this stupid, clunky way of downloading these samples.


prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063570
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063571
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063572
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063573
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063574
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063575
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063576
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063577
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063578
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063579
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063580
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063581
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063582
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063583
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063600
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063601
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063602
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063603
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063604
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063608
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063609
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063620
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063621
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063622
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063623
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063624
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063625
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063626
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063627
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063636
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063637
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063638
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063639
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063640
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063645
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063647
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063648
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063649
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063650
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063651
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063728
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063731
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063732
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063733
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063734
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063735
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063736
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063737
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063755
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063756
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063757
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063758
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063759
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063764
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063765
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063766
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063771
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063772
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063773
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063774
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063779
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063780
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063781
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063782
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063783
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063784
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063785
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063791
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063795
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063796
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063797
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063798
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063799
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063801
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063812
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063813
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063814
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063819
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063820
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063826
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063827
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063828
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063829
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063833
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063834
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063835
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063836
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063837
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063838
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063839
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063840



EOF

# ./sratoolkit.sh | bsub
