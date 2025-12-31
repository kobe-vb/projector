# Canvas Projector (Raspberry Pi)

Dit project is gemaakt om **snel een foto te projecteren op een canvas** zodat de **contouren kunnen worden overgetekend**.

Het systeem draait op een **Raspberry Pi** die aangesloten is op een **beamer** en wordt automatisch gestart bij het opstarten van de Pi.

---

## Overzicht

Het project bestaat uit twee delen die **tegelijk** draaien:

### 🖥️ Pygame (beamer output)
- Draait in de **main thread** (nodig voor display)
- Toont de geüploade foto fullscreen via de beamer
- Foto kan:
  - verplaatst worden
  - ingezoomd worden
  - aangepast worden via hoeken (contouren)

### 🌐 Flask server (webinterface)
- Draait in een **aparte thread**
- Serveert een eenvoudige, mooie website
- Laat toe om:
  - een foto te uploaden
  - edit mode aan / uit te zetten
  - Raspberry Pi te rebooten of afsluiten
