-- Calendário diário exigido pelo MetricFlow para agrupar métricas por dia, mês ou ano.
-- Cobre todo o período dos balanços (DFP desde 2010) com folga.
select dia::date as date_day
from generate_series('2009-01-01'::date, '2027-12-31'::date, interval '1 day') as dia
