from django.db import models

# --- Tablas de Configuración y Listas ---

class ListaValor(models.Model):
    lva_cdgo = models.IntegerField(primary_key=True, db_column='LVA_CDGO')
    lva_nombre = models.CharField(max_length=64, db_column='LVA_NOMBRE')
    lva_descr = models.CharField(max_length=256, blank=True, null=True, db_column='LVA_DESCR')
    lva_estdo = models.CharField(max_length=1, db_column='LVA_ESTDO')

    class Meta:
        db_table = 'lva_listavalor'

class ListaValorDetalle(models.Model):
    lvd_cdgo = models.IntegerField(primary_key=True, db_column='LVD_CDGO')
    lva = models.ForeignKey(ListaValor, on_delete=models.DO_NOTHING, db_column='LVA_CDGO', null=True)
    lvd_valor = models.CharField(max_length=32, db_column='LVD_VALOR')
    lvd_etiqta = models.CharField(max_length=128, db_column='LVD_ETIQTA')
    lvd_estdo = models.CharField(max_length=1, db_column='LVD_ESTDO')

    class Meta:
        db_table = 'lvd_listavalordetalle'

# --- Usuarios y Roles ---

class UsuarioSistema(models.Model):
    usu_cdgo = models.IntegerField(primary_key=True, db_column='USU_CDGO')
    usu_nombre = models.CharField(max_length=64, db_column='USU_NOMBRE')
    usu_passwd = models.CharField(max_length=256, db_column='USU_PASSWD')
    usu_estdo = models.CharField(max_length=1, db_column='USU_ESTDO')

    class Meta:
        db_table = 'usu_usuariosistema'

class Rol(models.Model):
    rol_cdgo = models.IntegerField(primary_key=True, db_column='ROL_CDGO')
    usu = models.ForeignKey(UsuarioSistema, on_delete=models.DO_NOTHING, db_column='USU_CDGO', null=True)
    rol_nombre = models.CharField(max_length=64, db_column='ROL_NOMBRE')
    rol_descr = models.CharField(max_length=256, db_column='ROL_DESCR')

    class Meta:
        db_table = 'rol_rol'

# --- Núcleo del Sistema (Atención y Préstamos) ---

class PrestamoRecurso(models.Model):
    prs_cdgo = models.IntegerField(primary_key=True, db_column='PRS_CDGO')
    prs_fchent = models.DateTimeField(db_column='PRS_FCHENT')
    prs_fchdev = models.DateTimeField(blank=True, null=True, db_column='PRS_FCHDEV')
    prs_obs = models.CharField(max_length=512, blank=True, null=True, db_column='PRS_OBS')

    class Meta:
        db_table = 'prs_prestamorecurso'

class Satisfaccion(models.Model):
    sat_cdgo = models.IntegerField(primary_key=True, db_column='SAT_CDGO')
    sat_calif = models.IntegerField(db_column='SAT_CALIF')
    sat_cmntrio = models.CharField(max_length=512, blank=True, null=True, db_column='SAT_CMNTRIO')
    sat_fecha = models.DateTimeField(db_column='SAT_FECHA')

    class Meta:
        db_table = 'sat_satisfaccion'

class Atencion(models.Model):
    atn_cdgo = models.IntegerField(primary_key=True, db_column='ATN_CDGO')
    sat = models.ForeignKey(Satisfaccion, on_delete=models.DO_NOTHING, db_column='SAT_CDGO', null=True)
    prs = models.ForeignKey(PrestamoRecurso, on_delete=models.DO_NOTHING, db_column='PRS_CDGO', null=True)
    atn_fecha = models.DateField(db_column='ATN_FECHA')
    atn_hrini = models.TimeField(db_column='ATN_HRINI')
    atn_hrfin = models.TimeField(db_column='ATN_HRFIN')
    atn_estdo = models.CharField(max_length=1, db_column='ATN_ESTDO')
    atn_obs = models.CharField(max_length=512, blank=True, null=True, db_column='ATN_OBS')

    class Meta:
        db_table = 'atn_atencion'

# --- Ciudadanos y Operadores ---

class Ciudadano(models.Model):
    ciu_cdgo = models.IntegerField(primary_key=True, db_column='CIU_CDGO')
    atn = models.ForeignKey(Atencion, on_delete=models.DO_NOTHING, db_column='ATN_CDGO', null=True)
    ciu_tpodoc = models.CharField(max_length=32, db_column='CIU_TPODOC')
    ciu_numdoc = models.CharField(max_length=32, db_column='CIU_NUMDOC')
    ciu_nmbres = models.CharField(max_length=128, db_column='CIU_NMBRES')
    ciu_aplldos = models.CharField(max_length=128, db_column='CIU_APLLDOS')
    ciu_fchancm = models.DateField(db_column='CIU_FCHANCM')
    ciu_genro = models.CharField(max_length=32, db_column='CIU_GENRO')
    ciu_etnia = models.CharField(max_length=64, db_column='CIU_ETNIA')
    ciu_nvleduc = models.CharField(max_length=64, db_column='CIU_NVLEDUC')
    ciu_ocpcion = models.CharField(max_length=64, db_column='CIU_OCPCION')
    ciu_estdo = models.CharField(max_length=1, db_column='CIU_ESTDO')
    ciu_email = models.CharField(max_length=128, db_column='CIU_EMAIL')
    ciu_tlfno = models.CharField(max_length=32, db_column='CIU_TLFNO')

    class Meta:
        db_table = 'ciu_ciudadano'

class Operador(models.Model):
    opr_cdgo = models.IntegerField(primary_key=True, db_column='OPR_CDGO')
    usu = models.ForeignKey(UsuarioSistema, on_delete=models.DO_NOTHING, db_column='USU_CDGO', null=True)
    atn = models.ForeignKey(Atencion, on_delete=models.DO_NOTHING, db_column='ATN_CDGO', null=True)
    opr_tpodoc = models.CharField(max_length=32, db_column='OPR_TPODOC')
    opr_numdoc = models.CharField(max_length=32, db_column='OPR_NUMDOC')
    opr_nmbres = models.CharField(max_length=128, db_column='OPR_NMBRES')
    opr_aplldos = models.CharField(max_length=128, db_column='OPR_APLLDOS')
    opr_email = models.CharField(max_length=128, db_column='OPR_EMAIL')
    opr_tlfno = models.CharField(max_length=32, db_column='OPR_TLFNO')
    opr_estdo = models.CharField(max_length=1, db_column='OPR_ESTDO')

    class Meta:
        db_table = 'opr_operador'

# --- Recursos, Servicios y Puntos ---

class Recurso(models.Model):
    rec_cdgo = models.IntegerField(primary_key=True, db_column='REC_CDGO')
    prs = models.ForeignKey(PrestamoRecurso, on_delete=models.DO_NOTHING, db_column='PRS_CDGO', null=True)
    rec_tipo = models.CharField(max_length=64, db_column='REC_TIPO')
    rec_estdo = models.CharField(max_length=1, db_column='REC_ESTDO')

    class Meta:
        db_table = 'rec_recurso'

class Servicio(models.Model):
    srv_cdgo = models.IntegerField(primary_key=True, db_column='SRV_CDGO')
    atn = models.ForeignKey(Atencion, on_delete=models.DO_NOTHING, db_column='ATN_CDGO', null=True)
    srv_nombre = models.CharField(max_length=128, db_column='SRV_NOMBRE')
    srv_descr = models.CharField(max_length=512, blank=True, null=True, db_column='SRV_DESCR')
    srv_tipo = models.CharField(max_length=64, db_column='SRV_TIPO')
    srv_reqeqp = models.CharField(max_length=1, db_column='SRV_REQEQP')
    srv_estdo = models.CharField(max_length=1, db_column='SRV_ESTDO')

    class Meta:
        db_table = 'srv_servicio'

class PuntoViveDigital(models.Model):
    pvd_cdgo = models.IntegerField(primary_key=True, db_column='PVD_CDGO')
    srv = models.ForeignKey(Servicio, on_delete=models.DO_NOTHING, db_column='SRV_CDGO', null=True)
    rec = models.ForeignKey(Recurso, on_delete=models.DO_NOTHING, db_column='REC_CDGO', null=True)
    opr = models.ForeignKey(Operador, on_delete=models.DO_NOTHING, db_column='OPR_CDGO', null=True)
    atn = models.ForeignKey(Atencion, on_delete=models.DO_NOTHING, db_column='ATN_CDGO', null=True)
    pvd_dircion = models.CharField(max_length=128, db_column='PVD_DIRCION')
    pvd_barrio = models.CharField(max_length=64, db_column='PVD_BARRIO')
    pvd_estdo = models.CharField(max_length=1, db_column='PVD_ESTDO')
    pvd_correo = models.CharField(max_length=128, db_column='PVD_CORREO')

    class Meta:
        db_table = 'pvd_puntovivedigital'