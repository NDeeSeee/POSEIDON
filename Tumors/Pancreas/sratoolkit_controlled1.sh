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

prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063257
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063258
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063259
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063260
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063261
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063262
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063263
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063264
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063265
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063266
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063267
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063268
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063269
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063494
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063495
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063496
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063497
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063498
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063499
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063500
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063501
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063502
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063503
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063504
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063505
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063506
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063507
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063508
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063509
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063510
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063511
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063512
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063513
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063514
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063515
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063516
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063517
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063518
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063519
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063520
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063521
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063522
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063523
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063524
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063525
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063526
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063527
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063528
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063529
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063530
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063531
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063532
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063533
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063534
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063535
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063536
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063537
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063538
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063539
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063540
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063541
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063542
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063543
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063544
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063545
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063546
prefetch --ngc prj_40747_D41857.ngc --max-size 35000000 SRR30063547
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



EOF

# ./sratoolkit.sh | bsub
