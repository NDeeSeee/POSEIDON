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


prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063599
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063605
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063606
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063607
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063610
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063611
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063612
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063613
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063614
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063615
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063616
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063617
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063618
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063619
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063628
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063629
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063630
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063631
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063632
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063633
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063634
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063635
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063641
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063642
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063643
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063644
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063646
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063652
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063727
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063729
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063730
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063738
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063739
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063740
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063741
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063742
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063743
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063744
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063745
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063746
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063747
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063748
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063749
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063750
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063751
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063752
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063753
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063754
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063760
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063761
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063762
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063763
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063767
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063768
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063769
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063770
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063775
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063776
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063777
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063778
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063786
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063787
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063788
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


EOF

# ./sratoolkit.sh | bsub
