from bs4 import BeautifulSoup


EN = (
    {
        'variable': 'congressperson_name',
        'name': 'Congressperson Name',
        'desc': """Name used by the congressperson during his term in
            office. Usually it is composed by two elements: a given name and a
            family name; two given names; or two forename, except if the head
            of the Chamber of Deputies explicitly alter this rule in order to avoid
            confusion."""
    },
    {
        'variable': 'congressperson_id',
        'name': 'Unique Identifier of Congressperson',
        'desc': """Unique identifier number of a congressperson at the
            Chamber of Deputies."""
    },
    {
        'variable': 'congressperson_document',
        'name': 'Congressperson Document Number',
        'desc': """Document used to identify the congressperson at the
            Chamber of Deputies. May change from one term to another."""
    },
    {
        'variable': 'term',
        'name': 'Legislative Period Number',
        'desc': """Legislative period: 4 years period, the same period
            of the term of congresspeople. In the context of this allowance,
            it represents the initial year of the legislature. It is also used
            as part of the Congressperson Document Number since it changes in
            between legislatures."""
    },
    {
        'variable': 'state',
        'name': 'State',
        'desc': """In the context of this allowance it represents the
            state or federative unit that elected the congressperson; it is
            also used to define the value of the allowance to the
            congressperson."""
    },
    {
        'variable': 'party',
        'name': 'Party',
        'desc': """It represents the abbreviation of a party. Definition
            of party: it is an organization built by people with interests or
            ideologies in common. They form an association with the purpose of
            achieving power to implement a government program. They are legal
            entities, free and autonomous when it comes to their creation and
            self-organization, since they respect the constitutional
            commandments."""
    },
    {
        'variable': 'term_id',
        'name': 'Legislative Period Code',
        'desc': """Legislative period: 4 years period, the same period
            of the term of congresspeople. In the context of this allowance it
            represents the identifying code of the legislature, an ordinal
            number incremented by one each new legislature (e.g. the
            2011 legislature is the 54th legislature)."""
    },
    {
        'variable': 'subquota_number',
        'name': 'Subquota Number',
        'desc': """In the context of this allowance this is the code of
            the category group referring to the nature of the expense claimed
            by the congressperson's receipt, the receipt of what was debited
            from the congressperson's account."""
    },
    {
        'variable': 'subquota_description',
        'name': 'Subquota Description',
        'desc': """The description of the category group referring to
            the nature of the expense."""
    },
    {
        'variable': 'subquota_group_id',
        'name': 'Subquota Specification Number',
        'desc': """In the context of this allowance there are expenses
            under certain category groups that require further specifications
            (e.g. fuel). This variable represents the code of these detailed
            specification."""
    },
    {
        'variable': 'subquota_group_description',
        'name': 'Subquota Specification Description',
        'desc': """Description of the detailed specification required by
            certain category groups."""
    },
    {
        'variable': 'supplier',
        'name': 'Supplier',
        'desc': """Name of the supplier of the product or service
            specified by the receipt."""
    },
    {
        'variable': 'cnpj_cpf',
        'name': 'CNPJ/CPF',
        'desc': """CNPJ or CPF are identification numbers issued for,
            respectively, companies and people by Federal Revenue of Brazil.
            CNPJ are 14 digits long and CPF are 11 digits long. This field is
            the identification number (CNPJ or CPF) of the legal entity issuing
            the receipt. The receipt is a proof of the expense and is a valid
            document used to claim for a reimbursement."""
    },
    {
        'variable': 'document_number',
        'name': 'Document Number',
        'desc': """This field is the identifying number issued in the
            receipt, in the proof of expense declared by the congressperson in
            this allowance."""
    },
    {
        'variable': 'document_type',
        'name': 'Fiscal Document Type',
        'desc': """Type of receipt — 0 (zero) for bill of sale; 1 (one)
            for simple receipt; and 2 (two) to expense made abroad."""
    },
    {
        'variable': 'issue_date',
        'name': 'Issue Date',
        'desc': """Issuing date of the receipt."""
    },
    {
        'variable': 'document_value',
        'name': 'Document Value',
        'desc': """Value of the expense in the receipt. If it refers to
            fly tickets this value can be negative, meaning that it is a
            credit related to another fly tickets issued but not used by the
            congressperson (the same is valid for `net_value`)."""
    },
    {
        'variable': 'remark_value',
        'name': 'Remark Value',
        'desc': """Remarked value of the expense concerning the value of
            the receipt, or remarked value of the expense."""
    },
    {
        'variable': 'net_value',
        'name': 'Net Value',
        'desc': """Net value of the receipt calculated from the value of
            the receipt and the remarked value. This is the value that is going
            to be debited from the congressperson's account. If the category
            group is Telephone and the value is zero, it means the expense was
            franchised out."""
    },
    {
        'variable': 'month',
        'name': 'Month',
        'desc': """Month of the receipt. It is used together with the
            year to determine in which month the debt will be considered in the
            context of this allowance."""
    },
    {
        'variable': 'year',
        'name': 'Year',
        'desc': """Year of the receipt. It is used together with the
            month to determine in which month the debt will be considered in
            the context of this allowance."""
    },
    {
        'variable': 'installment',
        'name': 'Installment Number',
        'desc': """The number of the installment of the receipt. Used
            when the receipt has to be reimbursed in installments."""
    },
    {
        'variable': 'passenger',
        'name': 'Passenger',
        'desc': """Name of the passenger when the receipt refers to a
            fly ticket."""
    },
    {
        'variable': 'leg_of_the_trip',
        'name': 'Leg of the Trip',
        'desc': """Leg of the trip when the receipt refers to a fly
            ticket."""
    },
    {
        'variable': 'batch_number',
        'name': 'Batch Number',
        'desc': """In the context of this allowance the batch number
            refers to the cover number of a batch grouping receipts handed in
            to the Chamber of Deputies to be reimbursed. This data together with the
            reimbursement number helps in finding the receipt in the Lower
            House Archive."""
    },
    {
        'variable': 'reimbursement_number',
        'name': 'Reimbursement Number',
        'desc': """In the context of this allowance the reimbursement
            number points to document issued in the reimbursement process.
            This data together with the reimbursement number helps in finding
            the receipt in the Chamber of Deputies Archive."""
    },
    {
        'variable': 'reimbursement_value',
        'name': 'Reimbursement Value',
        'desc': 'Reimbursement value referring to the document value.'
    },
    {
        'variable': 'applicant_id',
        'name': 'Applicant Identifier',
        'desc': """Identifying number of a congressperson or the Chamber of Deputies
            leadership for the sake of transparency and accountability within
            this allowance."""
    }
)


def get_portuguese():
    """
    Returns a generator of dictionaries with variable, name and description in
    pt-BR (based on data/2016-08-08-datasets-format.html)
    """
    with open('data/2016-08-08-datasets-format.html', 'rb') as file_handler:
        parsed = BeautifulSoup(file_handler.read(), 'lxml')
        for row in parsed.select('.tabela-2 tr'):
            cells = row.select('td')
            if cells:
                var, name, desc = map(lambda x: x.text.strip(), cells)
                yield {
                    'variable': var,
                    'name': name,
                    'desc': desc
                }


def clean_up(s):
    """Remove new lines and indentation from a string."""
    return ' '.join(s.split())


def variable_block(count, pt, en):
    """
    Get the count (int) the pt version (dict) and en version (dict) and outputs
    a generator with markdown contents with all the variable info in both
    languages. The dict is expected to have three keys: variable, name & desc.
    """
    return (
        '',
        '## {}. {} (`{}`)'.format(count, en['name'], en['variable']),
        '',
        '| 🇧🇷   | 🇬🇧   |',
        '|:------:|:------:|',
        '| **{}** | **{}** |'.format(pt['name'], en['name']),
        '|  `{}`  |  `{}`  |'.format(pt['variable'], en['variable']),
        '|   {}   |   {}   |'.format(pt['desc'], clean_up(en['desc'])),
        ''
    )


def markdown():
    yield from (
        '# Quota for Exercising Parliamentary Activity (CEAP)',
        '',
        '> This file is auto-generated by `src/translation_table.py`.',
        '',
        'The following files are covered by this description:',
        '',
        '```',
        '2016-08-08-current-year.xz', '2016-08-08-last-year.xz', '2016-08-08-previous-years.xz',
        '```'
        '',
        'The Quota for Exercising Parliamentary Activity (aka CEAP) is a montly quota available exclusively for covering costs of deputies with the exercise of parliamentary activity. The [Bureau Act 43 of 2009 🇧🇷](http://www2.camara.leg.br/legin/int/atomes/2009/atodamesa-43-21-maio-2009-588364-norma-cd-mesa.html) describe the guidelines for its use.',
    )

    for index, contents in enumerate(zip(get_portuguese(), EN)):
        yield from variable_block(index + 1, *contents)


with open('data/2016-08-08-ceap-datasets.md', 'w') as file_handler:
    file_handler.write('\n'.join(markdown()))
