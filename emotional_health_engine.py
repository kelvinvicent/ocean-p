"""
Motor de scoring — Módulo de Salud Emocional
==============================================
Compuesto por sub-módulos INDEPENDIENTES (nunca se mezclan en un solo score):

  1. PHQ-9      (Patient Health Questionnaire-9)       — depresión           — validado, uso libre
  2. WHO-5       (Índice de Bienestar de la OMS)         — bienestar positivo — validado, uso libre
  3. PHQ-15      (Patient Health Questionnaire-15)       — síntomas somáticos — validado, uso libre
  4. GAD-7       (Generalized Anxiety Disorder-7)        — ansiedad           — validado, uso libre
  5. Rosenberg   (Escala de Autoestima de Rosenberg)     — autoestima         — validado, uso libre
  6. Sueño       — escala breve NO clínica, inspirada en PSQI simplificado (diseño propio)
  7. Contexto    — preguntas de opción múltiple SIN puntuación, solo insumo cualitativo del informe

IMPORTANTE — este módulo es una herramienta de CRIBADO DE APOYO, no un instrumento
diagnóstico. El resultado debe presentarse siempre junto con un aviso de que no
reemplaza una evaluación profesional, y con recursos de ayuda cuando corresponda.

IMPORTANTE — la ideación de autolesión se mide EXCLUSIVAMENTE con el ítem 9 del
PHQ-9 (instrumento validado). No se agregan ítems propios sobre este tema en
ningún otro sub-módulo, para no diluir la fiabilidad de la alerta de crisis.

Uso:
    from emotional_health_engine import score_assessment
    resultado = score_assessment(phq9_responses, gad7_responses, sleep_responses,
                                  who5_responses, phq15_responses, rosenberg_responses)
"""

from dataclasses import dataclass, field
from statistics import mean

# ----------------------------------------------------------------------
# 1. BANCO DE ÍTEMS (redacción oficial — no se debe modificar el texto clínico)
# ----------------------------------------------------------------------

PHQ9_ITEMS: dict[int, str] = {
    1: "Poco interés o placer en hacer las cosas",
    2: "Se ha sentido decaído(a), deprimido(a) o sin esperanzas",
    3: "Ha tenido dificultad para quedarse o permanecer dormido(a), o ha dormido demasiado",
    4: "Se ha sentido cansado(a) o con poca energía",
    5: "Sin apetito o ha comido en exceso",
    6: "Se ha sentido mal con usted mismo(a) — o que es un fracaso o que ha fallado a su familia",
    7: "Ha tenido dificultad para concentrarse en actividades como leer o ver televisión",
    8: "Se ha movido o hablado tan lento que otros lo han notado, o lo contrario: ha estado muy inquieto(a)",
    9: "Pensamientos de que estaría mejor muerto(a) o de hacerse daño de alguna manera",
}
# Escala de respuesta PHQ-9 y GAD-7: 0=Ningún día, 1=Varios días, 2=Más de la mitad de los días, 3=Casi todos los días

PHQ9_IMPACT_ITEM = (
    "Si marcó cualquiera de los problemas anteriores, ¿qué tan difícil se le ha hecho "
    "hacer su trabajo, atender su casa o relacionarse con otras personas? "
    "(0=Nada difícil, 1=Algo difícil, 2=Muy difícil, 3=Extremadamente difícil)"
)
# Este ítem es oficial del paquete PHQ-9 completo, pero NO se suma al puntaje total.

GAD7_ITEMS: dict[int, str] = {
    1: "Sentirse nervioso(a), ansioso(a) o con los nervios de punta",
    2: "No poder parar o controlar la preocupación",
    3: "Preocuparse demasiado por diferentes cosas",
    4: "Dificultad para relajarse",
    5: "Estar tan inquieto(a) que es difícil quedarse quieto(a)",
    6: "Molestarse o irritarse fácilmente",
    7: "Sentir miedo, como si algo terrible fuera a pasar",
}

SLEEP_ITEMS: dict[int, str] = {
    1: "Ha tenido dificultad para conciliar el sueño",
    2: "Se ha despertado durante la noche sin poder volver a dormirse",
    3: "Se ha despertado sintiéndose descansado(a)",   # ítem invertido (más frecuencia = mejor)
    4: "Ha necesitado dormir durante el día para compensar el sueño perdido",
}
SLEEP_REVERSE_ITEMS = {3}

CONTEXT_ITEMS: dict[str, list[str]] = {
    "carga_laboral_academica": ["Baja", "Manejable", "Alta", "Extrema"],
    "cambios_vida_recientes": ["Ninguno", "Uno", "Varios"],
    "red_apoyo_social": ["Fuerte", "Moderada", "Débil", "Inexistente"],
    "perdida_reciente": ["No", "Sí, hace menos de 3 meses", "Sí, hace más de 3 meses"],
    "situacion_financiera": ["Estable", "Algo de estrés", "Mucho estrés"],
    "acceso_apoyo_profesional": ["Sí", "No", "No estoy seguro/a"],
    "cambios_consumo_sustancias": ["Sin cambios", "Ha aumentado", "Ha disminuido", "Prefiero no responder"],
}
# Los ítems de contexto NO se puntúan. Se muestran tal cual en el informe como insumo cualitativo.


WHO5_ITEMS: dict[int, str] = {
    1: "Me he sentido alegre y de buen humor",
    2: "Me he sentido tranquilo(a) y relajado(a)",
    3: "Me he sentido activo(a) y enérgico(a)",
    4: "Me he despertado sintiéndome fresco(a) y descansado(a)",
    5: "Mi vida diaria ha estado llena de cosas que me interesan",
}
# Escala WHO-5: 0=En ningún momento, 1=Alguna vez, 2=Menos de la mitad del tiempo,
# 3=Más de la mitad del tiempo, 4=La mayor parte del tiempo, 5=Todo el tiempo
# (últimas 2 semanas). Ningún ítem se invierte — todos miden bienestar en sentido positivo.

PHQ15_ITEMS: dict[int, str] = {
    1: "Dolor de estómago",
    2: "Dolor de espalda",
    3: "Dolor en brazos, piernas o articulaciones (rodillas, caderas, etc.)",
    4: "Dolores de cabeza",
    5: "Dolor en el pecho",
    6: "Mareos",
    7: "Desmayos",
    8: "Sentir el corazón acelerado o palpitaciones",
    9: "Falta de aire",
    10: "Dolor o problemas durante las relaciones sexuales",
    11: "Estreñimiento, intestino irritable o diarrea",
    12: "Náuseas, gases o problemas digestivos",
    13: "Sentirse cansado(a) o con poca energía",
    14: "Problemas para dormir",
    15: "Dolor menstrual o problemas relacionados con la menstruación",  # solo aplica a mujeres
}
PHQ15_FEMALE_ONLY_ITEM = 15
# Escala PHQ-15: 0=Nada molesto, 1=Un poco molesto, 2=Mucho molesto (últimas 4 semanas)

ROSENBERG_ITEMS: dict[int, str] = {
    1: "Siento que soy una persona digna de aprecio, al menos en igual medida que los demás",
    2: "Siento que tengo varias cualidades buenas",
    3: "En general, me inclino a pensar que soy un fracaso/a",              # invertido
    4: "Soy capaz de hacer las cosas tan bien como la mayoría de la gente",
    5: "Siento que no tengo mucho de lo que estar orgulloso(a)",            # invertido
    6: "Tengo una actitud positiva hacia mí mismo(a)",
    7: "En general, estoy satisfecho(a) conmigo mismo(a)",
    8: "Desearía valorarme más a mí mismo(a)",                             # invertido
    9: "A veces me siento verdaderamente inútil",                          # invertido
    10: "A veces pienso que no sirvo para nada",                           # invertido
}
ROSENBERG_REVERSE_ITEMS = {3, 5, 8, 9, 10}
# Escala Rosenberg: 0=Muy en desacuerdo, 1=En desacuerdo, 2=De acuerdo, 3=Muy de acuerdo


# ─────────────────────────────────────────────────────────────────
# CHECKLISTS NO CLÍNICOS (sin puntaje, observación descriptiva)
# ─────────────────────────────────────────────────────────────────

COGNITIVE_CHECKLIST_ITEMS: dict[int, str] = {
    1: "He tenido dificultad para concentrarme en tareas simples",
    2: "Olvido cosas que normalmente recordaría con facilidad",
    3: "Siento que mi pensamiento es más lento de lo usual",
    4: "Me cuesta trabajo tomar decisiones aunque sean pequeñas",
    5: "Tengo dificultad para retener información nueva",
    6: "Me pierdo en mitad de conversaciones o lecturas",
    7: "Siento una sensación de 'niebla' o confusión mental",
    8: "Me cuesta iniciar tareas aunque sepa que debo hacerlas",
}

BEHAVIORAL_CHECKLIST_ITEMS: dict[int, str] = {
    1: "He reducido actividades que antes disfrutaba",
    2: "Me he aislado de amigos o familia",
    3: "He descuidado tareas del hogar, trabajo o estudio",
    4: "He perdido la motivación para salir de casa",
    5: "Como de forma diferente a lo habitual (mucho más o mucho menos)",
    6: "Me cuesta mantener una rutina diaria",
    7: "He pospuesto cosas importantes sin poder retomarlo",
    8: "Paso más tiempo de lo usual en cama o sin actividad",
}

IRRITABILITY_CHECKLIST_ITEMS: dict[int, str] = {
    1: "Me he irritado o molestado con facilidad, más de lo normal",
    2: "He tenido reacciones exageradas ante situaciones pequeñas",
    3: "Me siento con poca tolerancia hacia los demás",
    4: "He tenido conflictos o fricciones que no son habituales en mí",
}
# Los 3 checklists se procesan como lista de items marcados (sí/no).
# NO generan un "puntaje" — se muestran en el informe como observaciones
# descriptivas, nunca como un número con apariencia de precisión clínica.


# ----------------------------------------------------------------------
# 2. ESTRUCTURAS DE RESULTADO
# ----------------------------------------------------------------------

@dataclass
class ScaleResult:
    total_score: float
    severity_band: str
    is_clinically_validated: bool = True


@dataclass
class AssessmentResult:
    phq9: ScaleResult = None
    who5: ScaleResult = None
    phq15: ScaleResult = None
    gad7: ScaleResult = None
    rosenberg: ScaleResult = None
    sleep: ScaleResult = None
    functional_impact_score: int | None = None
    context_answers: dict[str, str] = field(default_factory=dict)
    crisis_alert: bool = False          # item 9 del PHQ-9 > 0
    professional_help_recommended: bool = False  # severidad alta en depresión y/o ansiedad
    disclaimer: str = (
        "Este resultado es una herramienta de cribado de apoyo y no constituye un "
        "diagnóstico clínico. Si tienes dudas sobre tu bienestar emocional, te "
        "recomendamos hablar con un profesional de salud mental."
    )


# ----------------------------------------------------------------------
# 3. VALIDACIÓN DE ENTRADA
# ----------------------------------------------------------------------

def _validate_scale(
    responses: dict[int, int], expected_items: set[int], scale_name: str, max_value: int = 3
) -> None:
    """Valida que estén todas las respuestas esperadas y que cada valor esté en rango 0..max_value.

    max_value varía por instrumento: PHQ-9/GAD-7/Sueño = 3, WHO-5 = 5, PHQ-15 = 2, Rosenberg = 3.
    Generalizar este parámetro evita duplicar la función de validación por cada escala nueva.
    """
    missing = expected_items - responses.keys()
    if missing:
        raise ValueError(f"[{scale_name}] Faltan respuestas para los ítems: {sorted(missing)}")
    valid_range = set(range(0, max_value + 1))
    out_of_range = [i for i, v in responses.items() if i in expected_items and v not in valid_range]
    if out_of_range:
        raise ValueError(
            f"[{scale_name}] Valores fuera de rango (deben ser 0-{max_value}) en ítems: {out_of_range}"
        )


# ----------------------------------------------------------------------
# 4. SCORING — PHQ-9 (Depresión)
# ----------------------------------------------------------------------

def score_phq9(responses: dict[int, int], impact_response: int | None = None) -> tuple[ScaleResult, bool, int | None]:
    """Devuelve (resultado_escala, alerta_de_crisis, puntaje_de_impacto_funcional).

    El ítem 9 se evalúa por separado para la alerta de crisis, además de
    sumarse normalmente al total (así lo especifica el instrumento oficial).
    """
    _validate_scale(responses, set(PHQ9_ITEMS.keys()), "PHQ-9")

    total = sum(responses[i] for i in PHQ9_ITEMS)
    severity = _phq9_severity_band(total)
    crisis_alert = responses[9] > 0  # regla de seguridad: aislada del total

    result = ScaleResult(total_score=float(total), severity_band=severity)
    return result, crisis_alert, impact_response


def _phq9_severity_band(total: int) -> str:
    if total <= 4:
        return "minima_o_ninguna"
    elif total <= 9:
        return "leve"
    elif total <= 14:
        return "moderada"
    elif total <= 19:
        return "moderadamente_severa"
    else:
        return "severa"


# ----------------------------------------------------------------------
# 5. SCORING — GAD-7 (Ansiedad)
# ----------------------------------------------------------------------

def score_gad7(responses: dict[int, int]) -> ScaleResult:
    _validate_scale(responses, set(GAD7_ITEMS.keys()), "GAD-7")
    total = sum(responses[i] for i in GAD7_ITEMS)
    severity = _gad7_severity_band(total)
    return ScaleResult(total_score=float(total), severity_band=severity)


def _gad7_severity_band(total: int) -> str:
    if total <= 4:
        return "minima_o_ninguna"
    elif total <= 9:
        return "leve"
    elif total <= 14:
        return "moderada"
    else:
        return "severa"


# ----------------------------------------------------------------------
# 5b. SCORING — WHO-5 (Bienestar)
# ----------------------------------------------------------------------

def score_who5(responses: dict[int, int]) -> ScaleResult:
    """El WHO-5 mide bienestar POSITIVO (no síntomas). Por eso, a diferencia de
    PHQ-9/GAD-7, un puntaje BAJO es la señal de alerta, no uno alto."""
    _validate_scale(responses, set(WHO5_ITEMS.keys()), "WHO-5", max_value=5)
    raw_sum = sum(responses[i] for i in WHO5_ITEMS)          # 0-25
    percentage = round(raw_sum * 4, 1)                        # 0-100, conversión oficial del instrumento
    severity = _who5_wellbeing_band(percentage)
    return ScaleResult(total_score=percentage, severity_band=severity)


def _who5_wellbeing_band(percentage: float) -> str:
    if percentage <= 28:
        return "bienestar_muy_reducido"   # punto de corte asociado a probable depresión
    elif percentage <= 50:
        return "bienestar_reducido"       # punto de corte oficial: sugiere evaluar más a fondo
    else:
        return "bienestar_adecuado"


# ----------------------------------------------------------------------
# 5c. SCORING — PHQ-15 (Síntomas somáticos)
# ----------------------------------------------------------------------

def score_phq15(responses: dict[int, int], is_female: bool = True) -> ScaleResult:
    """El ítem 15 (dolor menstrual) solo aplica a mujeres. Si is_female=False,
    ese ítem se excluye tanto de la validación como de la suma."""
    expected_items = set(PHQ15_ITEMS.keys())
    if not is_female:
        expected_items.discard(PHQ15_FEMALE_ONLY_ITEM)

    relevant_responses = {i: v for i, v in responses.items() if i in expected_items}
    _validate_scale(relevant_responses, expected_items, "PHQ-15", max_value=2)

    total = sum(relevant_responses[i] for i in expected_items)
    severity = _phq15_severity_band(total)
    return ScaleResult(total_score=float(total), severity_band=severity)


def _phq15_severity_band(total: int) -> str:
    if total <= 4:
        return "minima"
    elif total <= 9:
        return "baja"
    elif total <= 14:
        return "media"
    else:
        return "alta"


# ----------------------------------------------------------------------
# 5d. SCORING — Escala de Autoestima de Rosenberg
# ----------------------------------------------------------------------

def score_rosenberg(responses: dict[int, int]) -> ScaleResult:
    _validate_scale(responses, set(ROSENBERG_ITEMS.keys()), "Rosenberg", max_value=3)
    values = []
    for item_id, raw in responses.items():
        values.append((3 - raw) if item_id in ROSENBERG_REVERSE_ITEMS else raw)
    total = sum(values)
    severity = _rosenberg_band(total)
    return ScaleResult(total_score=float(total), severity_band=severity)


def _rosenberg_band(total: int) -> str:
    return "rango_normal" if total >= 15 else "autoestima_baja"


# ----------------------------------------------------------------------
# 6. SCORING — Sueño (NO clínico, diseño propio, se etiqueta como tal)
# ----------------------------------------------------------------------

def score_sleep(responses: dict[int, int]) -> ScaleResult:
    _validate_scale(responses, set(SLEEP_ITEMS.keys()), "Sueño")
    values = []
    for item_id, raw in responses.items():
        values.append((3 - raw) if item_id in SLEEP_REVERSE_ITEMS else raw)
    total = sum(values)
    severity = _sleep_quality_band(total)
    return ScaleResult(total_score=float(total), severity_band=severity, is_clinically_validated=False)


def _sleep_quality_band(total: int) -> str:
    if total <= 2:
        return "buena"
    elif total <= 5:
        return "regular"
    else:
        return "mala"


# ----------------------------------------------------------------------
# 7. ORQUESTADOR
# ----------------------------------------------------------------------

def score_assessment(
    phq9_responses: dict[int, int],
    gad7_responses: dict[int, int],
    sleep_responses: dict[int, int],
    who5_responses: dict[int, int] | None = None,
    phq15_responses: dict[int, int] | None = None,
    rosenberg_responses: dict[int, int] | None = None,
    is_female: bool = True,
    context_answers: dict[str, str] | None = None,
    impact_response: int | None = None,
) -> AssessmentResult:
    phq9_result, crisis_alert, functional_impact = score_phq9(phq9_responses, impact_response)
    gad7_result = score_gad7(gad7_responses)
    sleep_result = score_sleep(sleep_responses)

    who5_result = score_who5(who5_responses) if who5_responses is not None else None
    phq15_result = score_phq15(phq15_responses, is_female) if phq15_responses is not None else None
    rosenberg_result = score_rosenberg(rosenberg_responses) if rosenberg_responses is not None else None

    professional_help = (
        phq9_result.severity_band in ("moderadamente_severa", "severa")
        or gad7_result.severity_band == "severa"
    )

    return AssessmentResult(
        phq9=phq9_result,
        who5=who5_result,
        phq15=phq15_result,
        gad7=gad7_result,
        rosenberg=rosenberg_result,
        sleep=sleep_result,
        functional_impact_score=functional_impact,
        context_answers=context_answers or {},
        crisis_alert=crisis_alert,
        professional_help_recommended=professional_help,
    )


# ----------------------------------------------------------------------
# 8. CASOS DE PRUEBA MANUALES
# ----------------------------------------------------------------------

def _zeros(item_dict: dict) -> dict[int, int]:
    return {i: 0 for i in item_dict}


if __name__ == "__main__":
    print("=" * 60)
    print("CASO A — Todo en 0 (línea base saludable)")
    print("=" * 60)
    result_a = score_assessment(_zeros(PHQ9_ITEMS), _zeros(GAD7_ITEMS), _zeros(SLEEP_ITEMS))
    print(f"PHQ-9: {result_a.phq9.total_score} ({result_a.phq9.severity_band})")
    print(f"GAD-7: {result_a.gad7.total_score} ({result_a.gad7.severity_band})")
    print(f"Alerta de crisis: {result_a.crisis_alert}")
    assert result_a.phq9.severity_band == "minima_o_ninguna"
    assert result_a.crisis_alert is False
    print("✅ Caso A correcto\n")

    print("=" * 60)
    print("CASO B — Depresión y ansiedad severas, SIN ideación suicida")
    print("=" * 60)
    phq9_b = {i: 3 for i in PHQ9_ITEMS}
    phq9_b[9] = 0  # explícitamente sin ideación suicida
    result_b = score_assessment(phq9_b, {i: 3 for i in GAD7_ITEMS}, _zeros(SLEEP_ITEMS))
    print(f"PHQ-9: {result_b.phq9.total_score} ({result_b.phq9.severity_band})")
    print(f"Alerta de crisis: {result_b.crisis_alert}")
    print(f"Se recomienda ayuda profesional: {result_b.professional_help_recommended}")
    assert result_b.phq9.severity_band == "severa"
    assert result_b.crisis_alert is False
    assert result_b.professional_help_recommended is True
    print("✅ Caso B correcto — severidad alta detectada, sin falsa alarma de crisis\n")

    print("=" * 60)
    print("CASO C — EL CASO MÁS IMPORTANTE: puntaje total BAJO pero ítem 9 > 0")
    print("=" * 60)
    phq9_c = _zeros(PHQ9_ITEMS)
    phq9_c[9] = 1  # "varios días" con pensamientos de autolesión, resto en 0
    result_c = score_assessment(phq9_c, _zeros(GAD7_ITEMS), _zeros(SLEEP_ITEMS))
    print(f"PHQ-9 total: {result_c.phq9.total_score} ({result_c.phq9.severity_band})")
    print(f"Alerta de crisis: {result_c.crisis_alert}")
    assert result_c.phq9.severity_band == "minima_o_ninguna"  # el total NO lo captura
    assert result_c.crisis_alert is True  # pero la alerta SÍ lo captura
    print("✅ Caso C correcto — la alerta de crisis funciona aunque el total sea bajo")
    print("   (esto es exactamente la razón por la que el ítem 9 se evalúa por separado)\n")

    print("=" * 60)
    print("CASO D — WHO-5: bienestar máximo (todos los ítems en 5)")
    print("=" * 60)
    who5_d = {i: 5 for i in WHO5_ITEMS}
    result_d = score_who5(who5_d)
    print(f"WHO-5: {result_d.total_score}% ({result_d.severity_band})")
    assert result_d.total_score == 100.0
    assert result_d.severity_band == "bienestar_adecuado"
    print("✅ Caso D correcto — la conversión x4 a porcentaje funciona bien\n")

    print("=" * 60)
    print("CASO E — WHO-5: bienestar muy reducido (todos los ítems en 0)")
    print("=" * 60)
    who5_e = {i: 0 for i in WHO5_ITEMS}
    result_e = score_who5(who5_e)
    print(f"WHO-5: {result_e.total_score}% ({result_e.severity_band})")
    assert result_e.total_score == 0.0
    assert result_e.severity_band == "bienestar_muy_reducido"
    print("✅ Caso E correcto\n")

    print("=" * 60)
    print("CASO F — PHQ-15: usuario NO mujer, el ítem 15 debe excluirse")
    print("=" * 60)
    phq15_f = {i: 1 for i in PHQ15_ITEMS}  # incluye el ítem 15 en las respuestas enviadas
    result_f = score_phq15(phq15_f, is_female=False)
    print(f"PHQ-15 (excluyendo ítem 15): {result_f.total_score} ({result_f.severity_band})")
    assert result_f.total_score == 14.0  # 14 ítems x 1, no 15 x 1 = 15
    print("✅ Caso F correcto — el ítem exclusivo de mujeres no se sumó\n")

    print("=" * 60)
    print("CASO G — Rosenberg: autoestima alta, ítems positivos altos e invertidos bajos")
    print("=" * 60)
    rosenberg_g = {i: 3 for i in ROSENBERG_ITEMS}          # todos "muy de acuerdo"
    for reverse_item in ROSENBERG_REVERSE_ITEMS:
        rosenberg_g[reverse_item] = 0                       # "muy en desacuerdo" con frases negativas
    result_g = score_rosenberg(rosenberg_g)
    print(f"Rosenberg: {result_g.total_score} ({result_g.severity_band})")
    assert result_g.total_score == 30.0  # el máximo posible tras invertir
    assert result_g.severity_band == "rango_normal"
    print("✅ Caso G correcto — la inversión de ítems negativos funciona igual que en Sueño\n")

    print("=" * 60)
    print("CASO H — Rosenberg: autoestima baja (respuestas invertidas al revés del Caso G)")
    print("=" * 60)
    rosenberg_h = {i: 0 for i in ROSENBERG_ITEMS}           # todos "muy en desacuerdo"
    for reverse_item in ROSENBERG_REVERSE_ITEMS:
        rosenberg_h[reverse_item] = 3                        # "muy de acuerdo" con frases negativas
    result_h = score_rosenberg(rosenberg_h)
    print(f"Rosenberg: {result_h.total_score} ({result_h.severity_band})")
    assert result_h.total_score == 0.0
    assert result_h.severity_band == "autoestima_baja"
    print("✅ Caso H correcto\n")

    print("=" * 60)
    print("CASO I — score_assessment() completo, con los 6 instrumentos a la vez")
    print("=" * 60)
    result_i = score_assessment(
        phq9_responses=_zeros(PHQ9_ITEMS),
        gad7_responses=_zeros(GAD7_ITEMS),
        sleep_responses=_zeros(SLEEP_ITEMS),
        who5_responses={i: 5 for i in WHO5_ITEMS},
        phq15_responses=_zeros(PHQ15_ITEMS),
        rosenberg_responses=rosenberg_g,
        is_female=True,
    )
    print(f"PHQ-9: {result_i.phq9.severity_band} | WHO-5: {result_i.who5.severity_band} | "
          f"PHQ-15: {result_i.phq15.severity_band} | Rosenberg: {result_i.rosenberg.severity_band}")
    assert result_i.who5 is not None and result_i.phq15 is not None and result_i.rosenberg is not None
    print("✅ Caso I correcto — el orquestador integra los 6 instrumentos sin conflicto\n")

    print("Todos los casos de prueba pasaron correctamente.")
