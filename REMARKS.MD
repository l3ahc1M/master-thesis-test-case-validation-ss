# Remarks

 1. Prozentwerte manchmal 1.5% oder 0,015
 2. Periods manchmal "1 month" oder "P1M"
 3. Plural Resourcen wie BankAccountEntryBalanceBasedRestrictions/1 sind listen. Welcher Wert aus der Liste kann ohne vorherigen Aufruf nur geraten sein
 4. "Prüfe das Ergebnis" wird nie gemacht. Überprüfung wird bei Asynchronen Prozessen schwierig, ansonsten direkt "GET" aufruf
 5. Leerer Body oft in den Beispielen. Wird natürlich nicht funktionieren weil alle Informationen fehlen.
 6. UUID manchmal keine UUID (layout)