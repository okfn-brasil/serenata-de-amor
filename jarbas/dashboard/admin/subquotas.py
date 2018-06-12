class Subquotas:

    EN_US = (
        'Maintenance of office supporting parliamentary activity',
        'Locomotion, meal and lodging',
        'Fuels and lubricants',
        'Consultancy, research and technical work',
        'Publicity of parliamentary activity',
        'Purchase of office supplies',
        'Software purchase or renting; Postal services; Subscriptions',
        'Security service provided by specialized company',
        'Flight tickets',
        'Telecommunication',
        'Postal services',
        'Publication subscriptions',
        'Congressperson meal',
        'Lodging, except for congressperson from Distrito Federal',
        'Automotive vehicle renting or watercraft charter',
        'Aircraft renting or charter of aircraft',
        'Automotive vehicle renting or charter',
        'Watercraft renting or charter',
        'Taxi, toll and parking',
        'Terrestrial, maritime and fluvial tickets',
        'Participation in course, talk or similar event',
        'Flight ticket issue'
    )

    PT_BR = (
        'Manutenção de escritório de apoio à atividade parlamentar',
        'Locomoção, alimentação e  hospedagem',
        'Combustíveis e lubrificantes',
        'Consultorias, pesquisas e trabalhos técnicos',
        'Divulgação da atividade parlamentar',
        'Aquisição de material de escritório',
        'Aquisição ou loc. de software serv. postais ass.',
        'Serviço de segurança prestado por empresa especializada',
        'Passagens aéreas',
        'Telefonia',
        'Serviços postais',
        'Assinatura de publicações',
        'Fornecimento de alimentação do parlamentar',
        'Hospedagem ,exceto do parlamentar no distrito federal',
        'Locação de veículos automotores ou fretamento de embarcações',
        'Locação ou fretamento de aeronaves',
        'Locação ou fretamento de veículos automotores',
        'Locação ou fretamento de embarcações',
        'Serviço de táxi, pedágio e estacionamento',
        'Passagens terrestres, marítimas ou fluviais',
        'Participação em curso, palestra ou evento similar',
        'Emissão bilhete aéreo'
    )

    NUMBERS = (
        '1',
        '2',
        '3',
        '4',
        '5',
        '6',
        '7',
        '8',
        '9',
        '10',
        '11',
        '12',
        '13',
        '14',
        '15',
        '119',
        '120',
        '121',
        '122',
        '123',
        '137',
        '999'
    )

    OPTIONS = sorted(zip(NUMBERS, PT_BR), key=lambda t: t[1])

    PT_BR_TRANSLATIONS = dict(zip(EN_US, PT_BR))
    EN_US_TRANSLATIONS = dict(zip(PT_BR, EN_US))

    @classmethod
    def pt_br(cls, en_us):
        return cls.PT_BR_TRANSLATIONS.get(en_us)

    @classmethod
    def en_us(cls, pt_br):
        return cls.EN_US_TRANSLATIONS.get(pt_br)
