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


prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063548
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063549
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063550
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063551
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063554
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063555
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063556
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063557
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063558
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063559
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063560
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063561
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063562
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063563
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063564
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063565
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063566
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063584
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063585
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063586
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063587
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063588
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063589
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063590
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063591
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063592
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063593
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063594
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063595
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063596
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063597
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063598
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063789
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063790
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063792
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063793
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063794
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063800
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063802
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063803
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063804
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063805
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063806
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063807
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063808
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063809
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063810
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063811
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063815
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063816
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063817
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063818
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063821
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063822
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063823
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063824
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063825
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063830
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063831
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063832
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063255
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063256
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063493
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063552
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063553
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063567
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063568
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063569
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
