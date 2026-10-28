# Digtværkstedet

Åbn `/digte/rediger.html`. Indsæt din tekst, tilføj eventuelt en titel, og brug knapperne til formatering. Titlen er valgfri: Et tomt titelfelt giver ingen synlig overskrift over digtet. Første linje bruges som linktekst i oversigten og som forslag til adressen. Du skal ikke skrive kode. Indsætning fra Word og andre sider tager kun teksten med; anvend derefter fed, kursiv og indryk i værkstedet.

Gem digtfilen på din computer. Den slutter på `.digt.json`, men er en almindelig tekstfil, og editoren klarer dens indhold. Upload filen til `digte/tekster` i GitHub, og gem ændringen. Når den automatiske udgivelse er aktiveret, bygges både oversigten og digtets egen side automatisk.

For at rette et digt: hent dets fil fra GitHub, åbn den i værkstedet, ret og gem. Behold samme navn i adressen, hvis det skal være samme digt. Upload som erstatning. Gem dine digtfiler som din egen kopi. Editorens browserkladde er kun en ekstra hjælp, ikke en sikkerhedskopi.

"Vis digtet på digtsiden" styrer offentliggørelse. Et skjult digt bliver ikke kopieret til den byggede side. Filerne i et offentligt GitHub-repository kan dog læses af andre. Gem derfor private eller fortrolige kladder på din egen computer.

"Må også bruges som skiftende digt på forsiden" samler digtet i en pulje. Forsidens udseende og digt ændres ikke i denne version.

Rækkefølge: de laveste tal kommer først. Brug fx 10, 20 og 30, så der er plads til et nyt digt imellem.

## Opsætning før udgivelse

Denne version er lokal. GitHub Pages skal ved godkendt udgivelse bruge et build, der kører `python scripts/build_digte.py --output _site` og udgiver `_site`. Ingen nøgler eller adgang til GitHub gemmes i editoren. Det eksisterende eventdatasæt bevares. Digtfiler og scripts udgives ikke som en del af selve hjemmesiden.
