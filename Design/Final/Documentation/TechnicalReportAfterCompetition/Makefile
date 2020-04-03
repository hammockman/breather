tn: TechnicalNoteAfterCompetition.md
	pandoc --template manawa \
          --metadata author:"Manawa Ora Team" \
          --metadata logo:manawa-ora-logo.png \
          -s "TechnicalNoteAfterCompetition.md" \
         -o "main.pdf"
	pandoc --template manawa \
          -s ../AssemblyInstructions/Assembly\ Instructions.md \
             ../MaintenanceAndCleaningInstructions/MaintenanceAndCleaningInstructions.md \
          -o "app1.pdf"
	pandoc --template manawa \
          -s ../ValidationTesting/Monthly\ Validation\ Testing.md \
          -o "app3.pdf"
	gs -dNOPAUSE -sDEVICE=pdfwrite -sOUTPUTFILE=Ventilator_ManawaOra_TechnicalNoteAfterCompetition.pdf -dBATCH \
             main.pdf \
             app1.pdf \
             ../Elec/PID_001.pdf \
             ../Elec/LS-001.pdf \
             ../Elec/E-001.pdf \
             ../Elec/E-002.pdf \
             ../Elec/InputOutput.pdf \
             ../BillOfMaterials/Manufacturing\ BOM\ -\ Basic\ model.pdf \
             app3.pdf
