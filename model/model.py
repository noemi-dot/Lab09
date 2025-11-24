from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self._tour_attrazione={}
        self._tour_attrazioni={}
        self.attrazioni_usate_set=set()

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        #costruisce la mappa self._tour_attrazioni: {id_tour:id_attr...}

        # TODO
        relazioni = TourDAO.get_tour_attrazioni()
        self._tou_attrazioni={}

        for r in relazioni:
            id_tour = r["id_tour"]
            id_attr = r["id_attrazione"]

            if id_tour not in self._tour_attrazioni:
                self._tour_attrazioni[id_tour]=[]
                self._tour_attrazioni[id_tour].append(id_attr)


    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        # TODO
        # Filtra solo i tour della regione scelta
        self._tour_filtrati=[]
        for id_tour, tour in self.tour_map.items():
            if tour.id_regione == id_regione:
                self._tour_filtrati.append(id_tour, tour)

        self._ricorsione(0,[],0,0.0,0,set())

        costo_totale=0.0
        for tour in self._pacchetto_ottimo:
            costo_totale += float(tour.costo)
            id_tour=getattr(tour, "id", None)
            if id_tour is not None:
                attr_ids_this_tour=set(self._tour_attrazioni.get(id_tour, []))
                attr_ids_effettive=attr_ids_this_tour.intersection(self.attrazioni_usate_set)
                formattata=[]
                for attr in attr_ids_effettive:
                    a=self.attrazioni_map.get(attr)
                    if a is not None:
                        formattata.append(f"{a.nome}({a.valore_culturale})")
                tour.attrazioni=formattata
            else:
                tour.attrazioni=[]

        self._costp=costo_totale

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        if start_index >= len(self._tour_filtrati):
            if valore_corrente >self._valore_ottimo:
                self._valore_ottimo=valore_corrente
                self._pacchetto_ottimo=list(pacchetto_parziale)
                self.attrazioni_usate_set=set(attrazioni_usate)
            return

        self._ricorsione(start_index +1, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, set(attrazioni_usate))

        id_tour, tour_attributi= self._tour_filtrati[start_index]
        durata_aggiuntiva= int(tour_attributi.durata_giorni)
        costo_aggiuntivo=float(tour_attributi.costo)

        id_attrazioni_tour=set(self._tour_attrazioni.get(id_tour, []))
        if id_attrazioni_tour & attrazioni_usate:
            return

        id_nuove_attrazioni=list(id_attrazioni_tour)
        valore_aggiuntivo =0
        for id_attrazione in id_nuove_attrazioni:
            attributi_attrazione=self.attrazioni_map.get(id_attrazione)
            if attributi_attrazione is not None:
                valore_aggiuntivo += int(attributi_attrazione.valore_culturale)

        nuova_durata= durata_corrente + durata_aggiuntiva
        nuovo_costo=costo_corrente + costo_aggiuntivo

        if ((self._max_giorni is None) or (nuova_durata<=self._max_giorni)) and ((self._max_budget is None) or (nuovo_costo<=self._max_budget)):
            pacchetto_parziale.append(tour_attributi)
            new_used=set(attrazioni_usate)
            new_used.update(id_nuove_attrazioni)

        self._ricorsione(start_index + 1, pacchetto_parziale, nuova_durata, nuovo_costo, valore_corrente + valore_aggiuntivo, new_used)

        pacchetto_parziale.pop()
        return