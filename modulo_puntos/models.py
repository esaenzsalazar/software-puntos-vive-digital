from django.db import models


class ListaValor(models.Model):
    lva_cdgo = models.AutoField(primary_key=True, db_column='LVA_CDGO')
    lva_nombre = models.CharField(max_length=64, db_column='LVA_NOMBRE')
    lva_descr = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        db_column='LVA_DESCR'
    )
    lva_estdo = models.CharField(max_length=1, db_column='LVA_ESTDO')

    class Meta:
        managed = True
        db_table = 'lva_listavalor'

    def __str__(self):
        return self.lva_nombre


class ListaValorDetalle(models.Model):
    lvd_cdgo = models.AutoField(primary_key=True, db_column='LVD_CDGO')
    lva = models.ForeignKey(
        ListaValor,
        on_delete=models.DO_NOTHING,
        db_column='LVA_CDGO',
        null=True
    )
    lvd_valor = models.CharField(max_length=32, db_column='LVD_VALOR')
    lvd_etiqta = models.CharField(max_length=128, db_column='LVD_ETIQTA')
    lvd_estdo = models.CharField(max_length=1, db_column='LVD_ESTDO')

    class Meta:
        managed = True
        db_table = 'lvd_listavalordetalle'

    def __str__(self):
        return self.lvd_etiqta


class Operador(models.Model):
    ope_cdgo = models.AutoField(primary_key=True, db_column='OPE_CDGO')
    ope_nombre = models.CharField(max_length=64, db_column='OPE_NOMBRE')
    ope_identificacion = models.CharField(
        max_length=20,
        db_column='OPE_IDENTIFICACION',
        unique=True,
        null=True
    )
    ope_passwd = models.CharField(max_length=256, db_column='OPE_PASSWD')
    ope_estdo = models.CharField(max_length=1, default='A', db_column='OPE_ESTDO')

    class Meta:
        managed = True
        db_table = 'ope_operador'

    def __str__(self):
        return self.ope_nombre


class Ciudadano(models.Model):
    ciu_cdgo = models.AutoField(primary_key=True, db_column='CIU_CDGO')
    ciu_tpodoc = models.CharField(max_length=32, db_column='CIU_TPODOC')
    ciu_numdoc = models.CharField(max_length=32, unique=True, db_column='CIU_NUMDOC')
    ciu_nmbres = models.CharField(max_length=128, db_column='CIU_NMBRES')
    ciu_aplldos = models.CharField(max_length=128, db_column='CIU_APLLDOS')
    ciu_fchancm = models.DateField(db_column='CIU_FCHANCM')
    ciu_email = models.EmailField(
        max_length=128,
        db_column='CIU_EMAIL',
        null=True,
        blank=True
    )
    ciu_tlfno = models.CharField(
        max_length=32,
        db_column='CIU_TLFNO',
        null=True,
        blank=True
    )
    ciu_genro = models.CharField(max_length=32, db_column='CIU_GENRO')
    ciu_etnia = models.CharField(
        max_length=64,
        db_column='CIU_ETNIA',
        null=True,
        blank=True
    )
    ciu_nvleduc = models.CharField(
        max_length=64,
        db_column='CIU_NVLEDUC',
        null=True,
        blank=True
    )
    ciu_ocpcion = models.CharField(
        max_length=64,
        db_column='CIU_OCPCION',
        null=True,
        blank=True
    )
    ciu_discapacidad = models.BooleanField(default=False, db_column='CIU_DISCAPACIDAD')
    ciu_estrato = models.IntegerField(db_column='CIU_ESTRATO', null=True, blank=True)
    ciu_estdo = models.CharField(max_length=1, default='A', db_column='CIU_ESTDO')

    class Meta:
        managed = True
        db_table = 'ciu_ciudadano'

    def __str__(self):
        return f"{self.ciu_nmbres} {self.ciu_aplldos} - {self.ciu_numdoc}"


class Servicio(models.Model):
    srv_cdgo = models.AutoField(primary_key=True, db_column='SRV_CDGO')
    srv_nombre = models.CharField(max_length=128, db_column='SRV_NOMBRE')
    srv_tipo = models.CharField(max_length=64, db_column='SRV_TIPO')
    srv_estdo = models.CharField(max_length=1, default='A', db_column='SRV_ESTDO')

    class Meta:
        managed = True
        db_table = 'srv_servicio'

    def __str__(self):
        return self.srv_nombre


class Satisfaccion(models.Model):
    sat_cdgo = models.AutoField(primary_key=True, db_column='SAT_CDGO')
    sat_calif = models.IntegerField(db_column='SAT_CALIF')
    sat_cmntrio = models.TextField(
        db_column='SAT_CMNTRIO',
        null=True,
        blank=True
    )
    sat_fecha = models.DateTimeField(auto_now_add=True, db_column='SAT_FECHA')

    class Meta:
        managed = True
        db_table = 'sat_satisfaccion'

    def __str__(self):
        return f"Calificación: {self.sat_calif}"


class Atencion(models.Model):
    atn_cdgo = models.AutoField(primary_key=True, db_column='ATN_CDGO')
    ciu = models.ForeignKey(Ciudadano, on_delete=models.CASCADE, db_column='CIU_CDGO')
    srv = models.ForeignKey(
        Servicio,
        on_delete=models.SET_NULL,
        db_column='SRV_CDGO',
        null=True
    )
    sat = models.ForeignKey(
        Satisfaccion,
        on_delete=models.SET_NULL,
        db_column='SAT_CDGO',
        null=True
    )
    ope = models.ForeignKey(
        Operador,
        on_delete=models.SET_NULL,
        db_column='OPE_CDGO',
        null=True
    )
    atn_fecha = models.DateField(auto_now_add=True, db_column='ATN_FECHA')
    atn_hrini = models.TimeField(auto_now_add=True, db_column='ATN_HRINI')
    atn_hrfin = models.TimeField(db_column='ATN_HRFIN', null=True, blank=True)
    atn_estdo = models.CharField(max_length=1, default='A', db_column='ATN_ESTDO')

    class Meta:
        managed = True
        db_table = 'atn_atencion'

    def __str__(self):
        return f"Atención {self.atn_cdgo}"