#!/usr/bin/env python3
"""The three fill-in templates, defined once.

Each is emitted twice: as .docx so a landlord can put their own logo on it and
type into it, and as a print-ready PDF so front-line staff can fill one in on
paper. Defining the content here rather than in two files is what stops the two
formats drifting apart.
"""

# A section is (heading, kind, payload).
#   'fields' -> [(label, hint)]        a label/blank grid
#   'checks' -> [item, ...]            tick boxes
#   'note'   -> "text"                 small print
#   'letter' -> [(text, bold), ...]    a body of prose

REPORT_FORM = dict(
    stem='04-damp-and-mould-report-form',
    title='Damp & mould report form',
    strap='Complete at the point a contract-holder first reports damp or mould. '
          'The date below is the date the clock starts.',
    sections=[
        ('Property', 'fields', [
            ('Address', ''),
            ('Postcode', ''),
            ('Reference', 'Your property or job reference'),
            ('Tenure', 'Occupation contract — social / private / other'),
        ]),
        ('Contract-holder', 'fields', [
            ('Name', ''), ('Phone', ''), ('Email', ''),
            ('Best access times', ''),
        ]),
        ('When it was reported', 'fields', [
            ('Date reported', 'DD / MM / YYYY — the WHQS clock runs from awareness'),
            ('Time', ''),
            ('Reported how', 'Phone / email / portal / in person / other'),
            ('Taken by', 'Staff name'),
        ]),
        ('What is being reported', 'checks', [
            'Black spotted mould', 'Tide mark low on wall', 'Damp patch, one spot',
            'Blown or salty plaster', 'Water running in', 'Musty smell',
            'Condensation on windows', 'Rotten timber / skirting', 'Ceiling stain',
        ]),
        ('', 'fields', [
            ('Rooms affected', ''),
            ('How long present', 'Weeks / months / years — and whether it is worse in winter'),
            ('Worse after rain?', 'Yes / no / unsure — separates penetrating damp from condensation'),
            ('Previously reported?', 'Yes / no — if yes, when, and what was done'),
            ('Description', 'In the contract-holder’s own words where possible'),
        ]),
        ('Who is exposed — affects HHSRS severity', 'checks', [
            'Child under 5', 'Person over 65', 'Asthma / COPD',
            'Other respiratory condition', 'Immunosuppressed', 'Pregnant',
            'Disability affecting escape', 'None declared', 'Not asked',
        ]),
        ('', 'note',
         'Severity under the Housing Health and Safety Rating System is judged partly '
         'on who is exposed, so a vulnerable household scores higher. Record it at the '
         'point of report — it decides whether the 24-hour or the 10-working-day clock '
         'applies.'),
        ('Initial risk assessment', 'fields', [
            ('Harm likely imminent?', 'Yes → investigate within 24 hrs, remedy within a further 24 hrs'),
            ('Significant risk, not imminent?', 'Yes → investigate within 10 working days, remedy within a further 5'),
            ('Assessed by', ''),
            ('Date assessed', ''),
        ]),
    ])

INVESTIGATION = dict(
    stem='05-investigation-record',
    title='Investigation record',
    strap='One per reported case. Dated at every step, so the file itself evidences '
          'that the duty was met.',
    sections=[
        ('Case', 'fields', [
            ('Property / reference', ''),
            ('Contract-holder', ''),
            ('Date became aware', 'Carry across from the report form — the clock starts here'),
            ('Clock applied', '24 hours  /  10 working days'),
            ('Investigation due by', 'Calculate from the date above'),
        ]),
        ('Investigation', 'fields', [
            ('Date attended', ''),
            ('Attended by', 'Name and, for a specialist survey, certificate number'),
            ('Within timescale?', 'Yes / no — if no, say why here'),
            ('Access obtained?', 'Yes / no — record failed access attempts, with dates'),
        ]),
        ('Findings', 'fields', [
            ('Diagnosis', 'Condensation / penetrating damp / rising damp / leak / timber decay / other'),
            ('Evidence', 'Moisture readings, salt analysis, surface temperature and humidity, external defects'),
            ('Cause', 'What is letting the water in, or preventing it drying'),
            ('Is the dwelling fit?', 'Renting Homes (Fitness for Human Habitation) (Wales) Regulations 2022'),
            ('Structural engineer required?', 'Yes / no — where decay has reached joists, lintels or bearings'),
        ]),
        ('Works', 'fields', [
            ('Urgent', 'What must happen now, and by when'),
            ('Remedial', 'The repair that removes the moisture'),
            ('General maintenance', 'Gutters, pointing, ground levels — often the cheapest part of the fix'),
            ('Remedy due by', 'A further 5 working days, or 24 hrs where harm is imminent'),
            ('Date works completed', ''),
            ('Within timescale?', 'Yes / no'),
        ]),
        ('Where it could not be completed in time', 'fields', [
            ('Written summary sent?', 'Required within 5 working days — see template 06'),
            ('Date sent', ''),
            ('Sent by', ''),
        ]),
        ('Sign-off', 'fields', [
            ('Post-works check', 'Date, and whether the contract-holder confirms it is resolved'),
            ('Completed by', ''),
            ('Date closed', ''),
        ]),
        ('', 'note',
         'Social landlords in Wales must also publish their response times and report '
         'performance to the Welsh Government.'),
    ])

LETTER = dict(
    stem='06-contract-holder-summary-letter',
    title='Written summary to the contract-holder',
    strap='Template letter. Where a damp or mould case cannot be completed in time, '
          'the WHQS requires a written summary within 5 working days setting out what '
          'will be done and when.',
    sections=[
        ('', 'letter', [
            ('[Your organisation name and address]', 'grey'),
            ('[Contract-holder name]', 'grey'),
            ('[Property address]', 'grey'),
            ('[Date]', 'grey'),
            ('', ''),
            ('Dear [name],', ''),
            ('Damp and mould at [property address]', 'bold'),
            ('Thank you for reporting this. You told us about it on [date reported], '
             'and we inspected on [date attended].', ''),
            ('What we found. [Plain English — what the problem actually is and what is '
             'causing it. Avoid blaming the household unless the survey genuinely '
             'supports it: cold wall surfaces, broken extract ventilation and windows '
             'that will not open are building defects, not lifestyle.]', ''),
            ('What we are going to do. [List the works, in order.]', ''),
            ('When. [Give real dates for each item. If any part depends on something '
             'outside your control — scaffolding, a specialist, a part on order — say '
             'so and give your best date.]', ''),
            ('What we need from you. [Access dates, or anything the household can '
             'helpfully do in the meantime. Be clear this is not a condition of the '
             'repair.]', ''),
            ('While the work is outstanding. [Any interim measures — a dehumidifier, a '
             'temporary heater, mould treatment, or a decant where it comes to that.]', ''),
            ('If you are not happy with this. You can contact us at [contact details] '
             'and ask us to look at it again. If you remain unhappy after our '
             'complaints process, you can take the matter to the Public Services '
             'Ombudsman for Wales, which is free and independent.', ''),
            ('Yours sincerely,', ''),
            ('[Name, role, contact details]', 'grey'),
        ]),
        ('', 'note',
         'Keep a copy on the case file and record the date sent on the investigation '
         'record. A dated written summary is the evidence that the duty was met even '
         'where the works ran over.'),
    ])

ALL = [REPORT_FORM, INVESTIGATION, LETTER]

DISCLAIMER = ('GENERAL GUIDANCE ONLY — NOT LEGAL ADVICE. The WHQS timescales apply to '
              'social landlords in Wales from 1 April 2026. Private landlords are bound '
              'instead by the continuous fitness duty in the Renting Homes (Wales) Act '
              '2016. Wales only — the rules in England, Scotland and Northern Ireland '
              'differ. Last reviewed 16 August 2026.')
