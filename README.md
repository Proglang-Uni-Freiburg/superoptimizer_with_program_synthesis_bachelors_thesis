# superoptimizer_with_program_synthesis

Arbeitstitel: Superoptimizer mittels Programmsynthese


Mit der Arbeit wollen wir ein Verfahren finden, mit dem optimierte Instruktionssequenzen für Ausdrücke mittels Programmsynthese gefunden werden. Der Startpunkt ist eine unoptimierte Sequenz, gesucht ist eine kürzere (oder schnellere) Sequenz, die die gleiche Funktion berechnet. Vorschlag: betrachte Instruktionssequenzen für RISC-V.


Mögliche Vorgehensweise  
    • Schreibe einen einfachen Codegenerator für arithmetische Ausdrücke (64bit Arithmetik), der bottom-up die Knoten des Ausdrucks in Register “verwandelt”. D.h. Konstanten werden in temporäre Register geladen, Operationen werden auf den Argumentregistern ausgeführt und das Ergebnis in ein Register abgelegt.  
    • Erzeuge aus einem Ausdruck Code und versuche dann mittels Programmsynthese äquivalenten Code zu finden. Verwende SMT zum Testen der Äquivalenz.   
    • Spätere Fragen: wie kann man den Suchraum intelligent einschränken? Wie kann man die Suche durch feedback vom SMT-Solver steuern?  
    • Später: Verfeinerung des Codegenerators, falls sinnvoll für den Befehlssatz: Konstanten c werden symbolisch behandelt und mit einem Konstraint wie 0<=c<256 versehen.  
    • Später: logische Operationen? Gleitkomma (zur Optimierung von Code für ML Anwendungen oder Simulation)?  
