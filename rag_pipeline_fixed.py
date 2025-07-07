#!/usr/bin/env python3
"""
Comprehensive RAG Pipeline Script for Multilingual Document Processing
"""

import os
import uuid
import logging
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import Json
import numpy as np
from sentence_transformers import SentenceTransformer
from ctransformers import AutoModelForCausalLM, AutoConfig


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Document content variables (Complete content from provided files)
TEB_DOCUMENT_CONTENT = """
## Genel Tanıtım ve İçindekiler
MÜŞTERİ KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AYDINLATMA METİNLERİ. Türk Ekonomi Bankası A.Ş. tarafından veri sorumlusu sıfatıyla müşteri edinimi ve hesap açılışı/kullanımı, kredi, yatırım ve sigorta faaliyetleri kapsamında kişisel verilerin işlenmesi hakkındaki aydınlatma metinleri aşağıda listelenmektedir. İlgilendiğiniz bankamız ürün veya hizmetlerine ilişkin aydınlatma metnini inceleyerek kişisel verilerinizin ilgili ürün veya hizmet kapsamında işlenmesi hakkında detaylı bilgi edinebilirsiniz. Ana başlıklar: Müşteri Edinimi Ve Hesap Açılışı/Kullanımı, Kredi Süreçleri, Yatırım Faaliyetleri, Sigorta Faaliyetleri. Banka Bilgileri: Türk Ekonomi Bankası A.Ş. İnkılap Mahallesi, Sokullu Caddesi, No:7A Ümraniye/İSTANBUL, Ticaret Sicil No: 189356, Mersis No: 0876004342000105, www.teb.com.tr.

## Bölüm 1: Müşteri Edinimi ve Hesap Açılışı/Kullanımı
Bu bölüm, MÜŞTERİ EDİNİMİ VE HESAP AÇILIŞI/KULLANIMI KAPSAMINDA KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ'dir.
### 1. Amaç ve Kapsam
Bu Aydınlatma Metni, Türk Ekonomi Bankası A.Ş. (“TEB”) olarak 6698 sayılı Kişisel Verilerin Korunması Kanunu (“KVKK”) uyarınca veri sorumlusu sıfatıyla hareket ettiğimiz kişisel veri işleme faaliyetlerini açıklamaktadır. Kişisel verilerinizin KVKK temel ilkelerine uygun şekilde işlenmesi, gizliliğinin ve güvenliğinin sağlanması konusunda her türlü özeni gösteriyoruz. Bu metin, işlenen kişisel verileriniz, toplanma yöntemleri, hukuki sebepleri, amaçları, aktarıldığı kişi/kurumlar ve KVKK uyarınca sahip olduğunuz haklar hakkında sizleri bilgilendirmek amacıyla hazırlanmıştır. Bankamızın ana faaliyetlerine ilişkin aydınlatma metinlerine https://www.teb.com.tr/kvk adresinden ulaşabilirsiniz.
### 2. İşlenen Kişisel Veri Kategorileriniz
TEB tarafından işlenen kişisel veri kategorileri şunlardır: Kimlik Verileri (Ad soyad, anne-baba adı, TCKN, pasaport no), İletişim Verileri (Ev/iş adresi, e-posta, telefon), Aile ve Yakın Bilgileri (Medeni durum, çocuk sayısı), Eğitim, İş ve Profesyonel Yaşama İlişkin Veriler (Meslek, çalışma geçmişi), Finansal Ürünlere, Varlıklara ve Finansal Duruma İlişkin Veriler (Gelir, mal varlığı, kredi geçmişi), Müşterilerin Finansal İşlemlerine İlişkin Veriler (Hesap hareketleri, kart kullanım bilgisi, dekontlar), Kartlı Sistem Ödeme Bilgileri (Kredi/banka kartı numarası, son kullanma tarihi, güvenlik kodu), Dijital Ortam Kullanım Verileri (Çerez kayıtları, IP adresi, cihaz bilgisi), İşlem Güvenliği ve Kurumun Siber Güvenliğine İlişkin Veriler (Kullanıcı adı, şifre, log kayıtları), Risk Yönetimine ve Finansal Güvenliğe İlişkin Veriler (Müşterini tanı bilgileri, kredi risk skoru), Görsel ve İşitsel Kayıtlar (Çağrı merkezi/telefon kayıtları, görüntülü görüşme kayıtları), Kişiyi Belirleyen Referans Değerler (Müşteri numarası, işlem numarası), Talep/Şikâyet ve İtibar Yönetimi Verileri (Talep ve şikayetler, yanıtları), Hukuki İşlem Verileri (Dava, yasal takip dosyaları), Fiziksel Mekan Güvenliğine İlişkin Veriler (Ziyaretçi giriş/çıkış, kamera kayıtları), Lokasyon Verisi (Konum bilgisi), Pazarlama Verileri (Kullanım alışkanlıkları, anket sonuçları). Özel nitelikli kişisel veri olarak ise Ceza Mahkûmiyeti ve Güvenlik Tedbirleri (Adli sicil ve mahkumiyet bilgileri) verileriniz, özellikle suç gelirlerinin aklanması, terörün finansmanı gibi finansal güvenlik süreçlerinin yönetimi amacıyla işlenebilecektir.
### 3. Kişisel Verilerinizin Elde Edilme Yöntemleri
Kişisel verileriniz, TEB tarafından doğrudan sizden veya üçüncü kişilerden otomatik ya da otomatik olmayan yöntemlerle elde edilebilir. Doğrudan sizden elde etme yöntemleri; şube, satış ekipleri, çağrı merkezi, SMS, e-posta gibi kanallarla sözlü/yazılı görüşmeler (otomatik olmayan) ve mobil/internet bankacılığı, ATM, web siteleri, CCTV gibi sistemler (otomatik) aracılığıyladır. Üçüncü kişilerden elde etme yöntemleri ise; dış hizmet sağlayıcılar, iş ortakları, meslek odaları, kanunen yetkili kamu/özel kurumlar (BDDK vb.) ve temsilcileriniz (otomatik olmayan) ile Kimlik Paylaşım Sistemi, Adres Paylaşım Sistemi, TBB Risk Merkezi, Gelir İdaresi Başkanlığı gibi veri tabanları (otomatik) aracılığıyladır.
### 4. Kişisel Verilerinizin İşlenme Amaçları ve Hukuki Sebepleri
Kişisel verileriniz KVKK Madde 5 ve 6'da belirtilen hukuki sebeplere dayanılarak işlenir. Bu sebepler şunlardır: Kanunlarda Açıkça Öngörülmesi (KVKK m. 5/2-a) kapsamında yetkili kuruluşlara bilgi verme ve mevzuata uyum; TEB ile Aranızdaki Sözleşmenin Kurulması veya İfası İçin Gerekli Olması (KVKK m. 5/2-c) kapsamında müşteri hizmetleri, kimlik doğrulama ve sözleşme süreçlerinin yürütülmesi; Hukuki Yükümlülüklerimizi Yerine Getirebilmek İçin İşlenmesi (KVKK m. 5/2-ç) kapsamında finansal güvenlik, denetim ve risk yönetimi; Bir Hakkın Tesisi, Kullanılması veya Korunması İçin İşlenmesi (KVKK m. 5/2-e) kapsamında dava ve yasal takip süreçleri; Meşru Menfaatlerimiz İçin Zorunlu Olması (KVKK m. 5/2-f) kapsamında banka stratejilerinin oluşturulması ve sistem geliştirme; Kişisel Verilerinizin İşlenmesine Açık Rıza Vermiş Olmanız (KVKK m. 5/1) kapsamında çapraz satış, kişiye özel reklam/promosyon faaliyetleri. Özel nitelikli veriler olan Ceza Mahkumiyeti verileri ise Kanunlarda Öngörülmesi (KVKK m. 6/3) hukuki sebebine dayalı olarak finansal güvenlik ve denetim amaçlarıyla işlenir.
### 5. Kişisel Verilerinizin Aktarıldığı Üçüncü Taraflar ve Aktarım Amaçları
Kişisel verileriniz; Hukuken Bilgi/Belge Almaya Yetkili Kamu/Özel Kurum veya Kuruluşları (BDDK, SPK, TCMB, MASAK, TBB Risk Merkezi, Mahkemeler vb.), Dış Hizmet veya Destek Hizmeti Sağlayan Kuruluşlar (Arşiv, Kart Basım, Çağrı Merkezi, Denetim vb.), İş Ortakları ve TEB Grubu, Yurtiçi ve Yurtdışı Bankalar ve Finans Kuruluşları ile Kartlı Ödeme Sistemleri (Mastercard, Visa vb.), ve Doğrudan veya Dolaylı TEB Hissedarları ile BNP Paribas Grubu'na aktarılabilir. Aktarım amaçları arasında yasal yükümlülüklerin yerine getirilmesi, sözleşmenin ifası, bankanın ticari faaliyetlerini sürdürmesi, pazarlama ve çapraz satış, risk yönetimi ve konsolide finansal tablo hazırlama gibi konular yer almaktadır.
### 6. Sahip Olduğunuz Haklar
KVKK'nın 11'inci maddesi uyarınca haklarınız şunlardır: Kişisel verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, işlenme amacını ve uygun kullanılıp kullanılmadığını öğrenme, verilerin aktarıldığı üçüncü kişileri bilme, eksik veya yanlış işlenmişse düzeltilmesini isteme, işlenmesini gerektiren sebeplerin ortadan kalkması halinde silinmesini/yok edilmesini isteme, otomatik sistemler vasıtasıyla aleyhinize bir sonuç çıkarsa itiraz etme, ve kanuna aykırı işlenmesi sebebiyle zarara uğramanız halinde zararın giderilmesini talep etme. Başvurularınızı TEB web sitesindeki form ile şubelerimize, noter veya iadeli taahhütlü posta yoluyla, güvenli elektronik imzalı e-posta ile kvkkbasvuru@teb.com.tr adresine veya KEP hesabından turkekonomibankasi@hs03.kep.tr adresine iletebilirsiniz. Talepleriniz en geç otuz gün içinde sonuçlandırılacaktır.

## Bölüm 2: Kredi Süreçleri
Bu bölüm, KREDİ SÜREÇLERİ KAPSAMINDA MÜŞTERİ KİŞİSEL VERİLERİNİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ'dir.
### 1. Amaç ve Kapsam
Bu metin, kredi süreçleri özelinde TEB'in veri sorumlusu olarak kişisel verilerinizi nasıl işlediğini açıklar ve genel bilgilendirme sağlar.
### 2. İşlenen Kişisel Veri Kategorileri
Kredi süreçleri için de Müşteri Edinimi bölümünde (Bölüm 1, Alt Başlık 2) listelenen tüm kişisel veri kategorileri geçerlidir.
### 3. Kişisel Verilerinizin Elde Edilme Yöntemleri
Genel yöntemlere ek olarak, kredi süreçleri için özellikle Türkiye Bankalar Birliği Risk Merkezi ve Kredi Kayıt Bürosu gibi kurumlardan da veri temin edilebilir.
### 4. Kişisel Verilerinizin İşlenme Amaçları ve Hukuki Sebepleri
Kredi süreçleri özelindeki amaçlar; kredi süreçlerine ilişkin risk yönetimi, kredi kullandırma ve tahsilat süreçlerinin yönetilmesi, POS süreçlerinin yürütülmesi gibi faaliyetleri içerir ve genel hukuki sebeplere dayanır.
### 5. Kişisel Verilerinizin Aktarıldığı Üçüncü Taraflar ve Aktarım Amaçları
Genel aktarım yapılan taraflara ek olarak, kredi süreçlerinde veriler alacakların devri amacıyla Varlık Yönetim Şirketleri'ne veya alacak satışı yapılan diğer şirketlere aktarılabilir.
### 6. Sahip Olduğunuz Haklar
Haklarınız ve başvuru yöntemleriniz, Müşteri Edinimi bölümünde (Bölüm 1, Alt Başlık 6) belirtilenlerle tamamen aynıdır.

## Bölüm 3: Yatırım Faaliyetleri
Bu bölüm, YATIRIM FAALİYETLERİ KAPSAMINDA MÜŞTERİ KİŞİSEL VERİLERİNİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ'dir.
### 1. Amaç ve Kapsam
Bu metin, yatırım faaliyetleri kapsamında TEB'in veri sorumlusu olarak kişisel verilerinizi nasıl işlediğini açıklar.
### 2. İşlenen Kişisel Veri Kategorileri
Yatırım faaliyetleri için de Müşteri Edinimi bölümünde (Bölüm 1, Alt Başlık 2) listelenen genel veri kategorileri geçerlidir.
### 3. Kişisel Verilerinizin Elde Edilme Yöntemleri
Genel yöntemlere ek olarak, yatırım faaliyetleri için Sermaye Piyasası Kurulu, Merkezi Kayıt Kuruluşu A.Ş. (MKK), portföy yönetim şirketleri ve yatırım fonları gibi kurumlardan da veri toplanabilir.
### 4. Kişisel Verilerinizin İşlenme Amaçları ve Hukuki Sebepleri
Yatırım faaliyetleri özelindeki amaçlar; emir iletimine aracılık, genel/sınırlı saklama hizmeti, işlem ve portföy aracılığı gibi yatırım hizmetlerinin operasyonel süreçlerinin yürütülmesi, SPK ve MKK gibi kurumlara raporlama yapılması ve mevzuata uyum gibi konuları içerir.
### 5. Kişisel Verilerinizin Aktarıldığı Üçüncü Taraflar ve Aktarım Amaçları
Genel aktarım yapılan taraflara ek olarak, yatırım faaliyetlerinde verileriniz Sermaye Piyasası Kurumu, Merkezi Kayıt Kuruluşu A.Ş., İstanbul Takas ve Saklama Bankası A.Ş. (Takasbank), Yatırımcı Tazmin Merkezi, emir iletimine aracılık edilen kurumlar, portföy yönetim şirketleri ve yatırım fonlarına aktarılabilir.
### 6. Müşterilerin Sahip Olduğu Haklar
Haklarınız ve başvuru yöntemleriniz, Müşteri Edinimi bölümünde (Bölüm 1, Alt Başlık 6) belirtilenlerle tamamen aynıdır.

## Bölüm 4: Sigorta Faaliyetleri
Bu bölüm, SİGORTA FAALİYETLERİ KAPSAMINDA MÜŞTERİ KİŞİSEL VERİLERİNİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ'dir.
### 1. Amaç ve Kapsam
Bu metin, TEB'in "veri sorumlusu" sıfatıyla yürüttüğü sigortacılık faaliyetlerini kapsar. TEB'in poliçe düzenleme gibi işlemlerde sigorta şirketinin "veri işleyeni" (acentesi) olarak hareket ettiği durumlar bu metnin kapsamı dışındadır ve ilgili sigorta şirketinin aydınlatma metnine tabidir.
### 2. İşlenen Kişisel Veri Kategorileri
Genel veri kategorileri işlenmektedir. Ancak, sağlık verileri gibi özel nitelikli kişisel veriler TEB tarafından yalnızca acente (veri işleyen) sıfatıyla hareket edilen durumlarda işlendiğinden bu metnin kapsamı dışındadır.
### 3. Kişisel Verilerinizin Elde Edilme Yöntemleri
Genel yöntemlere ek olarak, sigorta faaliyetleri için acentesi olunan sigorta şirketleri, Sigortacılık ve Özel Emeklilik Düzenleme ve Denetleme Kurumu (SEDDK) ve Sigorta Bilgi ve Gözetim Merkezi (SBM) gibi kurumlardan da veri temin edilebilir.
### 4. Kişisel Verilerinizin İşlenme Amaçları ve Hukuki Sebepleri
Sigorta faaliyetleri özelindeki amaçlar; sunulan ürün ve hizmetler arasında çapraz satış faaliyetleri gerçekleştirilmesi, size özel ürün ve hizmetlerin belirlenmesi, reklam/promosyon süreçlerinin yürütülmesi gibi pazarlama odaklı faaliyetleri içerir.
### 5. Kişisel Verilerinizin Aktarıldığı Üçüncü Taraflar ve Aktarım Amaçları
Genel aktarım yapılan taraflara ek olarak, sigorta faaliyetlerinde verileriniz Sigortacılık ve Özel Emeklilik Düzenleme ve Denetleme Kurumu ve Sigorta Bilgi ve Gözetim Merkezi gibi kurumlara aktarılabilir.
### 6. Sahip Olduğunuz Haklar
Haklarınız ve başvuru yöntemleriniz, Müşteri Edinimi bölümünde (Bölüm 1, Alt Başlık 6) belirtilenlerle tamamen aynıdır.
"""

BNP_PARIBAS_DOCUMENT_CONTENT = """
## Introduction
La protection de vos données personnelles est au cœur de nos préoccupations, le Groupe BNP Paribas a adopté des principes forts dans sa Charte de confidentialité des données personnelles. BNP Paribas Cardif (GIE BNP Paribas Cardif, Cardif Assurances Risques Divers et Cardif Assurance Vie) (« BNP Paribas Cardif » ou « nous »), en tant que responsable du traitement, est responsable de la collecte et du traitement de vos données personnelles dans le cadre de ses activités. L'objectif de la présente notice est de vous expliquer comment nous traitons vos données personnelles et comment vous pouvez les contrôler et les gérer. Le cas échéant, des informations complémentaires peuvent vous être communiquées directement au moment de la collecte de vos données personnelles.

## 1. ÊTES-VOUS CONCERNÉ PAR CETTE NOTICE ?
Vous êtes concernés par cette notice, si vous êtes notre client ou en relation contractuelle avec nous (souscripteur/adhérent, co-souscripteur/co-adhérent, assuré); un membre de la famille d'un client; une personne intéressée par nos produits ou services dès lors que vous nous communiquez vos données personnelles; un héritier ou ayant-droit; un co-emprunteur / garant; un représentant légal de notre client; un bénéficiaire d'une opération de paiement; un bénéficiaire d'un contrat ou d'une police d'assurance et d'un trust/une fiducie; un bénéficiaire effectif du bénéficiaire du Contrat; un bénéficiaire effectif d'un client personne morale; un dirigeant ou représentant légal d'un client personne morale; un donateur; un créancier (par exemple en cas de faillite); ou un actionnaire de société. Lorsque vous nous fournissez des données personnelles relatives à d'autres personnes, n'oubliez pas de les informer de la communication de leurs données et inviter les à prendre connaissance de la présente Notice.

## 2. COMMENT POUVEZ-VOUS CONTRÔLER LES TRAITEMENTS QUE NOUS RÉALISONS SUR VOS DONNÉES PERSONNELLES ?
Vous avez des droits qui vous permettent d'exercer un contrôle significatif sur vos données personnelles et sur la façon dont nous les traitons. Si vous souhaitez exercer les droits décrits ci-dessous, merci de nous envoyer une demande à: BNP Paribas Cardif – DPO, 8 rue du Port, 92728 Nanterre Cedex-France; ou Data.protection@Cardif.com; ou sur nos sites internet, lorsque cela est possible, avec un scan/copie de votre pièce d'identité lorsque cela est nécessaire. Si vous avez des questions, veuillez contacter notre Délégué à la protection des données aux mêmes adresses.
### 2.1. Vous pouvez demander l'accès à vos données personnelles
Si vous souhaitez avoir accès à vos données personnelles, nous vous fournirons une copie des données personnelles sur lesquelles porte votre demande ainsi que les informations se rapportant à leur traitement. Votre droit d'accès peut se trouver limité lorsque la réglementation le prévoit. C'est le cas de la réglementation relative à la lutte contre le blanchiment des capitaux et le financement du terrorisme qui nous interdit de vous donner directly accès à vos données personnelles traitées à cette fin. Dans ce cas, vous devez exercer votre droit d'accès auprès de la CNIL qui nous interrogera.
### 2.2. Vous pouvez demander la rectification de vos données personnelles
Si vous considérez que vos données personnelles sont inexactes ou incomplètes, vous pouvez demander qu'elles soient modifiées ou complétées. Dans certains cas, une pièce justificative pourra vous être demandée.
### 2.3. Vous pouvez demander l'effacement de vos données personnelles
Si vous le souhaitez, vous pouvez demander la suppression de vos données personnelles dans les limites autorisées par la loi.
### 2.4. Vous pouvez vous opposer au traitement de vos données personnelles fondé sur l'intérêt légitime
Si vous n'êtes pas d'accord avec un traitement fondé sur l'intérêt légitime, vous pouvez vous opposer à celui-ci, pour des raisons tenant à votre situation particulière, en nous indiquant précisément le traitement concerné et les raisons. Nous ne traiterons plus vos données personnelles sauf à ce qu'il existe des motifs légitimes et impérieux de les traiter ou que celles-ci sont nécessaires à la constatation, l'exercice ou la défense de droits en justice.
### 2.5. Vous pouvez vous opposer au traitement de vos données personnelles à des fins de prospection commerciale
Vous avez le droit de vous opposer à tout moment au traitement de vos données personnelles à des fins de prospection commerciale, y compris au profilage dans la mesure où il est lié à une telle prospection.
### 2.6. Vous pouvez suspendre l'utilisation de vos données personnelles
Si vous contestez l'exactitude des données que nous utilisons ou que vous vous opposez à ce que vos données soient traitées, nous procéderons à une vérification ou à un examen de votre demande. Pendant le délai d'étude de votre demande, vous avez la possibilité de nous demander de suspendre l'utilisation de vos données.
### 2.7. Vous avez des droits face à une décision automatisée
Par principe, vous avez le droit de ne pas faire l'objet d'une décision entièrement automatisée fondée sur un profilage ou non qui a un effet juridique ou vous affecte de manière significative. Nous pouvons néanmoins automatiser ce type de décision si elle est nécessaire à la conclusion/à l'exécution d'un contrat, autorisée par la réglementation ou si vous avez donné votre consentement. En toute hypothèse, vous avez la possibilité de contester la décision, d'exprimer votre point de vue et de demander l'intervention d'un être humain qui puisse réexaminer la décision.
### 2.8. Vous pouvez retirer votre consentement
Si vous avez donné votre consentement au traitement de vos données personnelles vous pouvez retirer ce consentement à tout moment.
### 2.9. Vous pouvez demander la portabilité d'une partie de vos données personnelles
Vous pouvez demander à récupérer une copie des données personnelles que vous nous avez fournies dans un format structuré, couramment utilisé et lisible par machine. Lorsque cela est techniquement possible, vous pouvez demander à ce que nous transmettions cette copie à un tiers.
### 2.10. Comment déposer une plainte auprès de la CNIL?
En plus des droits mentionnés ci-dessus, vous pouvez introduire une réclamation auprès de l'autorité de contrôle compétente, qui est le plus souvent celle de votre lieu de résidence, telle que la CNIL (Commission Nationale de l'Informatique et de Libertés) en France.

## 3. POURQUOI ET SUR QUELLE BASE LÉGALE UTILISONS-NOUS VOS DONNÉES PERSONNELLES ?
L'objectif de cette section est de vous expliquer pourquoi nous traitons vos données personnelles et sur quelle base légale nous nous reposons pour le justifier.
### 3.1. Vos données personnelles sont traitées pour nous conformer à nos différentes obligations légales
Vos données personnelles sont traitées lorsque cela est nécessaire pour nous permettre de respecter les réglementations auxquelles nous sommes soumis, notamment les réglementations propres aux activités d'assurance et financières. Nous utilisons vos données pour contrôler les opérations, prévenir la fraude, gérer les risques, lutter contre la déshérence, évaluer l'adéquation des produits (DDA), lutter contre la fraude fiscale, à des fins comptables, gérer les risques de RSE, prévenir la corruption, respecter les règles sur la signature électronique, et répondre aux demandes des autorités.
### 3.1.2. Nous traitons aussi vos données personnelles pour lutter contre le blanchiment d'argent et le financement du terrorisme
Nous appartenons à un Groupe de banque-assurance qui doit disposer d'un système robuste de lutte contre le blanchiment d'argent et le financement du terrorisme (LCB/FT) au niveau de nos entités, et piloté au niveau central, ainsi que d'un dispositif permettant d'appliquer les décisions de sanctions locales, européennes ou internationales. Dans ce contexte, nous sommes responsables de traitement conjoints avec BNP Paribas SA. Les traitements mis en œuvre sont détaillés en annexe 1.
### 3.2. Vos données personnelles sont traitées pour exécuter un contrat auquel vous êtes partie ou des mesures précontractuelles prises à votre demande
Vos données personnelles sont traitées lorsqu'elles sont nécessaires à la conclusion ou l'exécution d'un contrat pour: définir votre profil de risque d'assurance et tarification; évaluer si nous pouvons vous proposer un produit; vous envoyer des informations à votre demande; vous fournir les produits souscrits; assurer la gestion de votre contrat (sinistres, indemnisation, etc.); répondre à vos demandes; souscrire à nos produits; assurer le règlement de votre succession; et gérer les incidents de paiement.
### 3.3. Vos données personnelles sont traitées pour répondre à notre intérêt légitime ou celui d'un tiers
Lorsque nous fondons un traitement sur l'intérêt légitime, nous opérons une pondération entre cet intérêt et vos intérêts ou droits fondamentaux.
### 3.3.1. Dans le cadre de notre activité d'assureur, nous utilisons vos données personnelles pour :
Gérer les risques auxquels nous sommes exposés (conserver des preuves, surveiller les transactions pour la fraude, procéder à des recouvrements, traiter les réclamations, développer des modèles de risque); améliorer la cybersécurité et la continuité des activités; prévenir les dommages via la vidéosurveillance; améliorer l'automatisation de nos processus (ex: acceptation automatique des sinistres); réaliser des opérations financières (ventes de portefeuilles, titrisations); faire des études statistiques à des fins commerciales, de sécurité, de conformité et d'efficacité; organiser des opérations promotionnelles et des enquêtes de satisfaction.
### 3.3.2. Nous utilisons vos données personnelles pour vous envoyer des offres commerciales
En tant qu'entité du Groupe BNP Paribas, nous voulons vous offrir l'accès à notre gamme de produits. Dès lors que vous êtes client et sauf opposition, nous pourrons vous adresser des offres par voie électronique pour nos produits et services et ceux du Groupe similaires à ceux que vous avez déjà. Nous pourrons aussi vous adresser par téléphone et courrier postal, sauf opposition, les offres concernant nos produits et services ainsi que ceux du Groupe et de nos partenaires de confiance.
### 3.3.3. Nous analysons vos données personnelles pour réaliser un profilage standard
Pour améliorer votre expérience, nous établissons un profil standard à partir des données que vous nous avez communiquées ou issues de votre utilisation de nos canaux. Sauf opposition, nous réaliserons cette personnalisation basée sur un profilage standard.
### 3.3.4. Vos données personnelles sont traitées si vous y avez consenti
Pour certains traitements, nous vous demanderons votre consentement. Notamment pour: une personnalisation sur-mesure de nos offres; toute offre électronique pour des produits non similaires; la personnalisation basée sur vos comptes chez nos partenaires; l'utilisation de données de navigation (cookies) à des fins commerciales; le traitement de données de santé (pour évaluer le risque) ou de croyances religieuses (pour contrats d'obsèques); et pour toute prise de décision entièrement automatisée.

## 4. QUELS TYPES DE DONNÉES PERSONNELLES COLLECTONS-NOUS ?
Nous collectons différents types de données personnelles vous concernant, y compris: Données d'identification (nom, genre, date de naissance, nationalité, photo); Informations de contact (adresse postale, e-mail); Informations sur votre situation patrimoniale et vie de famille (situation matrimoniale, composition du foyer); Moments importants de votre vie (mariage, enfants); Mode de vie (loisirs, voyages); Informations économiques, financières et fiscales (identifiant fiscal, revenus, patrimoine); Informations relatives à l'éducation et à l'emploi (catégorie socioprofessionnelle, profession, employeur); Informations en lien avec les produits et services (coordonnées bancaires, numéro de contrat, données de transaction); Données nécessaires au paiement (numéro de carte bancaire, RIB/IBAN); Données relatives à la détermination des préjudices (circonstances du sinistre, rapports d'expertise, taux d'invalidité); Le NIR (numéro de sécurité sociale français) pour la gestion de contrat et la lutte contre la fraude; Informations relatives aux déclarations de sinistres (historique); Données sur vos habitudes et préférences; Données collectées lors de nos interactions (commentaires, conversations, e-mails); Données de connexion et de suivi (cookies); Données de vidéoprotection et de géolocalisation; Données concernant vos appareils (adresse IP); Identifiants de connexion; Données révélant votre état de santé (questionnaires de santé); et Croyances religieuses et philosophiques (pour les contrats d'obsèques).

## 5. AUPRES DE QUI COLLECTONS-NOUS DES DONNÉES PERSONNELLES ?
Nous collectons des données personnelles directement auprès de vous, mais aussi auprès d'autres sources. Nous collectons parfois des données provenant de sources publiques (publications officielles, sites Internet/pages de réseaux sociaux d'entités juridiques, presse). Nous collectons aussi des données personnelles de tierces parties (autres entités du Groupe BNP Paribas, nos clients, nos partenaires commerciaux, nos co-assureurs, prestataires de services d'initiation de paiement, prestataires spécialisés dans l'enrichissement de données, agences de prévention de la fraude, courtiers de données).

## 6. AVEC QUI PARTAGEONS-NOUS VOS DONNÉES PERSONNELLES ET POURQUOI ?
### 6.1. Avec les entités du Groupe BNP Paribas
En tant que société membre du Groupe BNP Paribas, nous collaborons étroitement avec les autres sociétés du groupe. Vos données personnelles pourront être partagées entre les entités du Groupe BNP Paribas, lorsque c'est nécessaire, pour: nous conformer à nos obligations légales et réglementaires; et répondre à nos intérêts légitimes (gérer la fraude, faire des études statistiques, améliorer la fiabilité des données, vous offrir l'accès à l'ensemble des produits et services du Groupe, personnaliser le contenu et les prix).
### 6.2. Avec les entités du Groupe BNP Paribas qui distribuent nos produits
Des échanges de données sont plus fréquents avec nos distributeurs intra-groupe lorsque vous souhaitez souscrire, avez souscrit, ou êtes bénéficiaire d'un contrat d'assurance Cardif distribué par une entité du Groupe. Ces données sont partagées pour adapter la distribution et les tarifs, proposer des garanties complémentaires, vérifier l'adéquation de votre profil, faciliter la conclusion des contrats, et digitaliser notre relation.
### 6.3. Avec des destinataires, tiers au Groupe BNP Paribas et des sous-traitants
Nous pouvons partager vos données avec: des sous-traitants (services informatiques, impression, recouvrement); des partenaires commerciaux; des agents indépendants, intermédiaires, institutions financières; des autorités financières, fiscales, administratives, pénales ou judiciaires; des prestataires de services de paiement tiers; certaines professions réglementées (avocats, notaires); des organismes de sécurité sociale; des agences de renseignement commercial; et des parties intéressées au contrat (détenteur, souscripteur, victimes).

## 7. TRANSFERTS INTERNATIONAUX DE DONNÉES PERSONNELLES
En cas de transferts internationaux depuis l'Espace économique européen (EEE) vers un pays n'appartenant pas à l'EEE, le transfert peut avoir lieu sur la base d'une décision d'adéquation de la Commission européenne. Si le pays n'a pas un niveau de protection adéquat, nous nous appuierons sur une dérogation applicable à votre situation ou nous prendrons des mesures comme les clauses contractuelles types pour assurer la protection de vos données.

## 8. PENDANT COMBIEN DE TEMPS CONSERVONS-NOUS VOS DONNÉES PERSONNELLES ?
Nous conservons vos données personnelles pendant la durée nécessaire au respect des législations et réglementations, ou pendant une durée définie au regard de nos contraintes opérationnelles (comptabilité, gestion de la relation client, défense en justice). Lorsqu'un contrat est conclu, les données sont en majorité conservées pendant la durée de la relation contractuelle plus la période légale de prescription (allant de 2 à 30 ans). En l'absence de contrat, vos données sont conservées 3 ans. Les données de santé collectées sans contrat sont conservées au maximum 5 ans. Les informations de carte bancaire sont conservées 13 mois. Les enregistrements téléphoniques sont conservés 6 mois.

## 9. COMMENT SUIVRE LES ÉVOLUTIONS DE CETTE NOTICE DE PROTECTION DES DONNÉES PERSONNELLES ?
Dans un monde où les technologies évoluent en permanence, nous revoyons régulièrement cette Notice et la mettons à jour si besoin. Nous vous invitons à prendre connaissance de la dernière version de ce document en ligne, et nous vous informerons de toute modification significative par le biais de notre site Internet ou via nos canaux de communication habituels.

## Annexe 1 : Traitement des données personnelles pour lutter contre le blanchiment d'argent et le financement du terrorisme
Nous appartenons à un Groupe bancaire qui doit disposer d'un système robuste de lutte contre le blanchiment d'argent et le financement du terrorisme (LCB/FT), piloté au niveau central, ainsi qu'un dispositif de lutte contre la corruption et pour le respect des Sanctions internationales. Dans ce contexte, nous sommes responsables de traitement conjoints avec BNP Paribas SA. A des fins de LCB/FT, nous mettons en œuvre les traitements suivants: Un dispositif de connaissance de la clientèle (KYC); Des mesures d'identification renforcées pour les clients à risque et les Personnes Politiquement Exposées (PPE); Des politiques pour ne pas entrer en relation avec des Banques fictives; Une politique de ne pas s'engager avec des personnes, entités ou territoires sous sanctions (Crimée/Sébastopol, Cuba, Iran, Corée du Nord, Syrie); Le filtrage de nos bases clients et transactions; Des systèmes pour détecter les opérations suspectes; et un programme de conformité contre la corruption. Pour ce faire, nous faisons appel à des prestataires externes (Dow Jones Factiva, World-Check) et aux informations publiques.

## Annexe 2 : Durées de conservation des données
Les durées de conservation correspondent aux délais pendant lesquels nous pouvons être amenés à traiter la donnée collectée.
### En l'absence de conclusion d'un contrat
Gestion de la prospection: 3 ans. Données de santé: 5 ans maximum (2 ans en base active, 3 ans en archivage). Statistiques de mesures d'audience (cookies): 13 mois, informations collectées 25 mois.
### Lorsqu'un contrat est conclu
La durée de conservation tient compte de la durée de l'engagement et du délai de prescription. Sur le plan comptable, les documents sont conservés 10 ans.
### Durées de conservation légales ou réglementaires
Documents fiscaux: 6 ans (parfois 10 ans). Documents LCB/FT: 5 ans. Contrats électroniques (>120€): 10 ans.
### Durées de conservation propres aux contrats d'assurance
Garanties Responsabilité Civile: En cas de sinistre matériel, 10 ans; corporel, 50 ans. En l'absence de sinistre, 12 ou 22 ans selon la base. Garanties dommages: 10 ans. Assurance vie (en cas de vie ou de décès): 30 ans. Assurance Emprunteur: 20 ans. Assurance complémentaire – Prévoyance: 20 ans. Assurance de produits affinitaires: 5 ans.
"""
BASEL_III_DOCUMENT_CONTENT = """
## Yönetici Özeti
Basel Bankacılık Denetim Komitesinin alt çalışma gruplarında uzun süredir üzerinde tartışılarak geliştirilen değişiklik önerileri 12 Eylül 2010 tarihli Merkez Bankası Başkanları ve Denetim Otoritesi Başkanları toplantısında da kabul edilmiş ve nihai uygulama kararları açıklanmıştır. Kurumumuzca Komiteye iletilen ve Ülkemiz bankacılık sektörünün uzun dönem istikrarına fayda sağlayacağını düşündüğümüz pek çok öneri kabul görerek Basel III uzlaşısı olarak da anılmaya başlanan düzenlemelerin içerisinde yer almıştır. 12 Eylül 2010 tarihi itibarıyla kamuoyuna açıklanan kurallar etkileri itibarıyla ciddi finansal sonuçlara yol açsa da sermaye yeterliliği hesaplama felsefesinde önemli sapmalar meydana getirmemektedir. Başka bir deyişle; Basel III, Basel II gibi sermaye gereksinimi hesaplanma usulünü tümden değiştiren bir "devrim" değil ancak Basel II‟nin özellikle son finansal krizdeki gözlemlenen eksikliklerini tamamlayan bir "ek düzenlemeler seti" niteliğindedir. Yeni kurallar setinde, mevcut özkaynak ve sermaye yeterliliği hesaplamasında önem arz eden sermayenin niteliğinin ve niceliğinin artırılmasına ilişkin standartlar ile dönemselliğe bağlı olarak kullanılacak ilave sermaye tamponu oluşturulması gibi başlıklar mevcuttur. Bahsi geçen hususlara ilave olarak daha önce Basel II uygulamalarının en büyük eksikliği olarak görülen likidite yeterlilik ve risk bazlı olmayan kaldıraç oranları gibi hususlarda yeni düzenlemeler ihdas edilmiştir. Bu çalışmanın amacı kamuoyunu Basel III kuralları ve bu kuralların Dünya ve Türkiye‟ye olası etkileri hususunda bilgilendirmektir.

## 1. Basel III Nedir?
Dünyanın yüzleştiği en büyük finansal krizlerden birisi olan son dönem gelişmeleri beraberinde, dışarıdan bakıldığında son derece detaylı ve karmaşık gözüken finansal düzenlemelerin yetersizliği tartışmalarını gündeme getirmiştir. Krizin ortaya çıkardığı eksiklikleri gidermek amacıyla yakın zamanda Basel III olarak adlandırılan düzenleme değişiklikleri gündeme gelmiştir. Basel III olarak adlandırılan düzenleme değişiklikleriyle ulaşılmak istenen hedefler şu şekilde özetlenebilir: Bankacılık sisteminin şoklara karşı dayanıklılığının artırılması, kurumsal yönetişim ve risk yönetimi uygulamalarının geliştirilmesi, bankaların şeffaflığının artırılması, mikro ve makro bazda düzenlemelerle finansal sistemin direncinin artırılması. Bu amaçların gerçekleştirilmesi için; hâlihazırda kullanılan asgari sermayenin nicelik ve niteliğinin artırılması, risk bazlı olmayan bir kaldıraç oranı getirilmesi, sermaye ihtiyacının ekonominin çevrim dönemlerine göre ayarlanabilmesi, asgari likidite oranları düzenlenmesi, alım-satım hesapları ve karşı taraf kredi riski hesaplamalarında değişiklik yapılması yönünde çalışmalar yapılmıştır. Bu revizyonlar, Basel II'yi tümden değiştiren bir "devrim" değil, onun eksikliklerini tamamlayan bir "ek düzenlemeler seti" niteliğindedir. Basel III, yeni finansal düzenlemelerin tek parçası olmayıp, koordinasyon Finansal İstikrar Kurulu (FSB) tarafından yapılmaktadır. Öne çıkan düzenlemeler: Daha Nitelikli Sermaye (çekirdek sermayenin kalitesinin artırılması), Niceliği Artırılmış Sermaye (çekirdek sermaye oranının %7'ye, Tier 1'in %8,5'e yükseltilmesi), Sermaye Tamponu Oluşturulması (%0-%2,5 arası ilave), Risk Bazlı Olmayan Kaldıraç Oranı (%3 hedefi), ve Likidite Düzenlemeleri (Likidite Karşılama Oranı ve Net İstikrarlı Fonlama Oranı). Düzenlemelere tam uyumun 2013-2019 arasında gerçekleştirilmesi planlanmaktadır.

## 2. Basel III'ün Ortaya Çıkış Süreci Nasıl Gelişmiştir?
Haziran 2004'te yayımlanan Basel II metni, 2006'da AB müktesebatına dahil edilmiştir. Ancak Eylül 2008'deki Lehman Brothers iflası ve takip eden küresel kriz, mevcut sistemin ciddi eksiklikler içerdiğini göstermiştir. Krizin maliyeti çok ciddi boyutlara ulaşmış, reel sektörü etkilemiş ve yüksek iş kayıpları yaşanmıştır. Bu durum, bankacılık sistemini gelecekteki krizlere karşı daha dirençli kılmak amacıyla likidite, sermaye kalitesi ve miktarının artırılması gibi önemli reformların gerekliliğini ortaya koymuştur. Basel Komitesi tarafından hazırlanan reform takvimi, Ekim 2009'da Pittsburgh'daki G20 liderler zirvesinde ele alınmış ve 12 Eylül 2010 tarihinde reformlar kamuoyuna duyurulmuştur. Bu reformlar, sadece bankaya özgü yükümlülükleri genişletmekle kalmayıp, sistemik riskleri telafi etmek için ilave yükümlülükler de getirmeyi planlamaktadır. Basel Komitesi, sistemik olarak önemli bankaların risklerinin tanımlanması hususunda Finansal İstikrar Kurulu (FSB) ile çalışmalarını yürütmektedir ve alım-satım hesapları, dışsal derecelendirme notlarının kullanımı, büyük riskler ve sınır ötesi bankacılık gibi alanlarda da çalışmalarına devam etmektedir.

## 3. Basel III Neler Getirmektedir?
### a- Özkaynaklar
Basel II'de yer alan özkaynakların kapsamı değiştirilmiştir. Üçüncü kuşak sermaye (Tier 3) uygulaması kaldırılmıştır. Ana sermaye (Tier 1) içinde yer alan ve zarar karşılama potansiyeli yüksek olan unsurlar çekirdek sermaye (common equity) olarak adlandırılmıştır. Çekirdek sermaye; ödenmiş sermaye, dağıtılmamış karlar, kar (zarar) ve diğer kapsamlı gelir tablosu kalemlerinden oluşmaktadır. Finansal kuruluşlara yapılan ve eşik değeri aşan yatırımlar, mortgage servis hizmetleri ve ertelenmiş vergi aktifi gibi düzenleyici ayarlamalar, 2014'ten başlayarak kademeli olarak 2018'de tamamen çekirdek sermayeden indirim kalemi olarak kullanılacaktır. Ana sermayenin çekirdek sermaye veya katkı sermaye içinde yer almayan diğer bileşenleri ise 10 yıllık bir süreçte tamamen sermaye bileşeni olmaktan çıkarılacaktır.
### b- Sermayeye İlişkin Oranlar
Asgari çekirdek sermaye oranı (Çekirdek Sermaye / RAV) 2013-2015 arasında kademeli olarak %2'den %4,5'a çıkarılacaktır. Aynı dönemde birinci kuşak sermaye oranı da %4'ten %6'ya çıkarılacaktır. %2,5'lik bir sermaye koruma tamponu, 2016-2019 arasında kademeli olarak eklenecektir. Bu tamponun sağlanamaması durumunda bankaların kar dağıtımına kısıtlamalar getirilecektir. Ayrıca, ülke şartlarına bağlı olarak %0 ilâ %2,5 arasında değişen bir döngüsel sermaye tamponu uygulaması getirilmiştir. Bu tampon, hızlı kredi büyümesinin önüne geçmeyi hedeflemektedir.
### c- Kaldıraç Oranı
Sermaye oranlarını destekleyici nitelikte, şeffaf ve risk bazlı olmayan bir kaldıraç oranı getirilmiştir. Oran, (Ana Sermaye / Aktifler + Bilanço Dışı Kalemler) formülüyle hesaplanacak olup, 2013-2017 arası paralel uygulama döneminde %3 oranı test edilecektir. Nihai hali 1 Ocak 2018'den itibaren "Birinci Yapısal Blok"a dahil edilecektir.
### d- Likidite Oranları
Likiditeye ilişkin olarak Likidite Karşılama Oranı (Liquidity Coverage Ratio - LCR) ve Net İstikrarlı Fonlama Oranı (Net Stable Funding Ratio - NSFR) isimli iki oran ihdas edilmiştir. LCR, bankanın likit varlıklarının 30 günlük net nakit çıkışlarına oranının minimum %100 olmasını gerektirir. NSFR ise bankaların orta ve uzun vadeli fonlama yapılarını güçlendirmeyi amaçlar ve "mevcut istikrarlı fonlama tutarının" "ihtiyaç duyulan istikrarlı fonlama tutarına" oranının en az %100 olmasını hedefler. LCR için 2011-2015, NSFR için 2012-2018 arası gözlem periyodu olarak belirlenmiştir.

## 4. Basel III'ün Küresel Ekonomiye Etkileri
2008 finansal krizi, birçok bankanın yetersiz sermaye ve likidite ile faaliyet gösterdiğini ortaya koymuştur. Basel III standartlarının yükseltilmesi faydalı görülse de, bu uygulamaların ne zaman ve nasıl yürürlüğe gireceği kritik bir sorudur. İlave sermaye ve likidite gereksinimi, bankaların kredi maliyetlerini artırmasına ve KOBİ'lere yönelik kredilerin azalmasına yol açabilir, bu da ekonomik büyümeyi olumsuz etkileyebilir. Bu endişeler nedeniyle, BIS tarafından uygulamalar geniş bir zaman dilimine (2013-2019) yayılmıştır. BIS tarafından yapılan çalışmalara göre, sermaye yeterliliğinde yapılacak bir puanlık artışın GSMH'da en fazla yaklaşık %0,19'luk bir gerilemeye neden olacağı tahmin edilmektedir. Gelişmekte olan ekonomilerin bu süreçten daha çok etkilenmesi beklenmektedir.

## 5. Basel III Düzenlemelerinin Türkiye'ye Olası Etkileri
Türk Bankacılık sisteminin sermaye yapısı, çekirdek sermaye kalemleri (ödenmiş sermaye, kar yedekleri) açısından güçlüdür. Haziran 2010 itibarıyla ana sermaye, toplam özkaynakların %91,2'sini oluşturmaktadır. Üçüncü kuşak sermaye (Tier 3) kalemi Türk Bankacılık Sektörü'nde zaten bulunmamaktadır. Türkiye'nin %8'lik yasal orana ek olarak 2006'da %12'lik bir hedef oran belirlemesi, kriz sürecinde bankaların sermaye sıkıntısı çekmemesinde etkili olmuştur. Türkiye, krizde bankacılık sektörüne kamunun sermaye desteğine ihtiyaç duymayan tek OECD ülkesi olmuştur. Haziran 2010 itibarıyla sektörün sermaye yeterliliği oranı %19,2'dir. BDDK'nın kriz öncesi aldığı proaktif önlemler (likidite yönetmeliği, hedef SYR) Basel III ile büyük ölçüde örtüşmektedir. Bu nedenle, Türkiye'nin sermaye yeterliliği oranının yüksekliği göz önüne alındığında, Basel III'ün büyüme üzerinde doğrudan olumsuz bir etkisinin olması mevcut durumda beklenmemektedir.

## 6. Basel III'e İlişkin Eleştiriler ve Endişeler
Bazı eleştirmenler, Basel III kurallarının 2008 krizinin gerçek nedenini, yani risk ağırlıklandırmasındaki hataları ele almakta başarısız olduğunu savunmaktadır. Yüksek riskli portföylerin, türev ürünler ve Credit Default Swaps (CDS) gibi araçlarla düşük riskli gibi gösterilmesinin Basel II'nin en zayıf halkası olduğu belirtilmektedir. Bu nedenle bazıları, Basel III'ün yerel bankaları Wall Street'in hataları nedeniyle cezalandırdığını düşünmektedir. Diğer endişeler arasında Denetim Arbitrajı (ülkeler arası yasal boşluklardan faydalanma), uzun adaptasyon sürecinin yeni kurallara uyumu zorlaştırması ve bankaların yeni standartlara uyum stratejilerinin (sermaye artırımı, kar payı dağıtmama, faaliyet alanı değiştirme) küresel ekonomiyi olumsuz etkileme potansiyeli bulunmaktadır.

## Kaynakça
Bu bölümde BIS, BDDK, Dünya Gazetesi, Global Research, Firedoglake, mi2g.com, OECD ve TCMB tarafından yayımlanmış çeşitli rapor, makale ve belgelere atıfta bulunulmaktadır.

## Ek:1 Basel III Uygulama Takvimi
Uygulama takvimi, çeşitli oranların (Kaldıraç Oranı, Asgari Çekirdek Sermaye Oranı, Sermaye Koruma Tamponu, Asgari Birinci Kuşak Sermaye Oranı, Likidite Oranları) 2011 ile 2019 yılları arasında kademeli olarak nasıl uygulamaya alınacağını detaylandırmaktadır. Örneğin, Kaldıraç Oranı için 1 Ocak 2013 - 1 Ocak 2017 arası paralel uygulama ve 1 Ocak 2015'te kamuya açıklama öngörülmektedir. Asgari Çekirdek Sermaye Oranı %4,5'e, Sermaye Koruma Tamponu ise %2,5'e kademeli olarak yükseltilerek 2019'da toplamda %7'lik bir orana ulaşılacaktır. Likidite Karşılama Oranı (LCR) ve Net İstikrarlı Fonlama Oranı (NSFR) için ise gözlem periyotları belirlenmiş olup, bu periyotların sonunda asgari standartlar ilan edilecektir.
"""
BOA_DOCUMENT_CONTENT = """
## Submit your application
Now that you've found the home you want to buy and a lender to work with, the mortgage process begins. At this stage, your lender will have you fill out a full application and ask you to supply documentation relating to your income, debts and assets.

## Order a home inspection
Schedule a home inspection as soon as you can. Doing so will give you adequate time before your closing date to negotiate with the seller if the inspection reveals any unforeseen issues.
### Why do I need a home inspection?
A home inspection is an added expense that some first-time homebuyers don't expect and might feel safe declining, but professional inspectors often notice things most of us don't. This step is especially important if you're buying an existing home as opposed to a newly constructed home, which might come with a builder's warranty. If the home needs big repairs you can't see, an inspection helps you negotiate with the current homeowner to have the issues fixed before closing or adjust the price accordingly so you have extra funds to address the repairs once you own the home. During the inspection, be sure to ask questions and bring a checklist of things you want information on. Note that a comprehensive inspection should not only bring defects and problem areas to your attention, it should also highlight the positive aspects of a home as well. When you receive the final report, prioritize the issues and decide whether you want to negotiate those items with the sellers. Remember: Every deal is different and negotiable.

## Be responsive to your lender
If you applied and qualify for a mortgage, you'll receive conditional approval. At this stage, your lender may require additional documentation. Make sure to respond promptly to keep your application moving forward.

## Purchase homeowner's insurance
Your lender will require proof of insurance before the loan can receive final approval.
### Know about exclusions to coverage
For example, most insurance policies do not cover flood or earthquake damage as a standard item. These types of coverage must be bought separately.
### Know about dollar limitations on claims
Even if you're covered for a risk, there may be a limit to how much the insurer will pay. For example, many policies limit the amount paid for stolen jewelry unless items are insured separately.
### Know the replacement cost
If your home is destroyed, you'll receive money to replace it only to the maximum of your coverage, so be sure your insurance is sufficient. This means that if your home is insured for $150,000 and it costs $180,000 to replace it, you'll only receive $150,000.
### Know the actual cash value
If you choose not to replace your home when it's destroyed, you'll receive the replacement cost, less depreciation. This is called actual cash value.
### Know the liability
Your homeowner's insurance will generally cover you for accidents that happen to other people on your property, including medical care, court costs and awards by the court. However, there's usually an upper limit to the amount of coverage provided – be sure your coverage is sufficient if you have significant assets.

## Let the process play out
Know what's happening behind the scenes: Your lender will order a home appraisal to ensure that the value of the home you're buying is in line with the purchase price. The appraiser will visit the home and compare it to other recently sold homes in a similar price range. Your lender will also order a title search to make sure there are no outstanding liens on the property.

## Avoid taking on new debt
While your loan is in process, avoid opening new credit cards or making other major financial changes. New loans or other changes that affect your debt-to-income ratio could get in the way of your mortgage approval.

## Lock in your rate
If you haven't already locked in your interest rate with your lender, you'll want to do so. Your rate must be locked in no later than 10 days prior to your closing date.

## Review your documents
Once your loan is approved and your inspection, appraisal and title search are complete, your lender will set a closing date and let you know exactly how much money you'll need to bring to your closing.

## Arrange to pay your down payment and closing costs
You'll need to get a cashier's check or arrange to wire money to cover your down payment and closing costs.

## Close on your home
At the closing, be sure to read all the documents you receive and ask any questions you may have about the terms of the agreement. Then, after you've signed everything, you can unlock the door and celebrate your new home!
"""


def parse_document(content: str, source_document: str, entity: str, language: str, 
                  document_type: str, main_section_prefix: str = "## ", 
                  sub_section_prefix: str = "### ") -> List[Dict[str, Any]]:
    """Parse document content into structured chunks with full content."""
    chunks = []
    main_sections = content.strip().split(main_section_prefix)

    for section in main_sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        main_title = lines[0].strip()
        sub_content_str = '\n'.join(lines[1:])
        sub_sections = sub_content_str.strip().split(sub_section_prefix)

        # Main section intro - TAM İÇERİK İLE
        main_intro_text = sub_sections[0].strip()
        if main_intro_text:
            full_text = f"Döküman: {source_document}\nKuruluş: {entity}\nDil: {language}\nTip: {document_type}\n\nAna Bölüm: {main_title}\n\nTam İçerik:\n{main_intro_text}"
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'source_document': source_document,
                'entity': entity,
                'language': language,
                'document_type': document_type,
                'main_section_title': main_title,
                'sub_section_title': 'Genel Açıklama',
                'text': full_text,
                'raw_text': main_intro_text
            })

        # Sub-sections - TAM İÇERİK İLE
        for sub_section in sub_sections[1:]:
            if not sub_section.strip():
                continue
            
            sub_lines = sub_section.strip().split('\n')
            sub_title = sub_lines[0].strip()
            text_content = '\n'.join(sub_lines[1:]).strip()
            print(text_content)
            
            full_text = f"Döküman: {source_document}\nKuruluş: {entity}\nDil: {language}\nTip: {document_type}\n\nAna Bölüm: {main_title}\nAlt Başlık: {sub_title}\n\nTam İçerik:\n{text_content}"
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'source_document': source_document,
                'entity': entity,
                'language': language,
                'document_type': document_type,
                'main_section_title': main_title,
                'sub_section_title': sub_title,
                'text': full_text,
                'raw_text': text_content
            })
            
    return chunks

def get_summary_from_yi(llm, text_content: str) -> str:
    """
    Yüklenen Yi-1.5-9B-Chat modelini kullanarak metin için detaylı bir özet oluşturur.
    """
    # Daha detaylı özet için geliştirilmiş prompt
    prompt = f"""
[INST]
Aşağıdaki metni kapsamlı bir şekilde özetle. Özet 5-7 cümle olsun ve şu kriterlere uygun olsun:
- Ana konuyu ve amacı açıkla
- Önemli detayları ve anahtar bilgileri dahil et
- Metnin bağlamını ve önemini vurgula
- Sadece özet metnini ver, başka açıklama ekleme

Metin:
"{text_content}"
[/INST]
"""
    try:
        # Modeli çalıştır ve yanıtı al - daha uzun özet için token sayısını artır
        response = llm(prompt, max_new_tokens=300, temperature=0.2, top_k=50, top_p=0.9, repetition_penalty=1.2)
        # Yanıtı temizle ve döndür
        return response.strip()
    except Exception as e:
        print(f"HATA: Özet oluşturulurken bir sorun oluştu - {e}")
        return "Detaylı özet oluşturulamadı."


def get_labels_from_yi(llm, text_content: str) -> List[str]:
    """
    Yüklenen Yi-1.5-9B-Chat modelini kullanarak metinden 4 adet etiket çıkarır.
    """
    # Daha kesin ve güvenilir etiket çıkarma prompt'u
    prompt = f"""
[INST]
Aşağıdaki metnin içeriğini en iyi şekilde tanımlayan 4 adet kısa ve öz anahtar kelime/etiket çıkar. 
Kurallar:
- Sadece 4 adet etiket
- Her etiket maksimum 2-3 kelime
- Virgülle ayırarak yaz
- Hiçbir açıklama ekleme
- Örnek format: "bankacılık, sermaye, likidite, düzenleme"

Metin:
"{text_content[:1000]}..."
[/INST]
"""
    try:
        # Modeli çalıştır - daha düşük temperature ile daha tutarlı sonuçlar
        response = llm(prompt, max_new_tokens=50, temperature=0.05, top_k=20, repetition_penalty=1.1)
        
        # Yanıtı temizle
        cleaned_response = response.strip()
        
        # Virgülle ayır ve temizle
        labels = []
        for label in cleaned_response.split(','):
            clean_label = label.strip().lower()
            # Boş olmayan ve çok uzun olmayan etiketleri al
            if clean_label and len(clean_label) > 1 and len(clean_label) < 30:
                labels.append(clean_label)
        
        # Tam olarak 4 etiket döndür
        if len(labels) >= 4:
            return labels[:4]
        else:
            # Yetersizse varsayılan etiketlerle tamamla
            while len(labels) < 4:
                labels.append("genel_etiket")
            return labels
            
    except Exception as e:
        print(f"HATA: Etiket oluşturulurken bir sorun oluştu - {e}")
        return ["etiket1", "etiket2", "etiket3", "etiket4"]
    
    
def setup_database(conn) -> None:
    """Set up database schema and extensions."""
    cursor = conn.cursor()
    
    try:
        # Enable pgvector extension
        logger.info("Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Check if table exists and drop if it has wrong vector dimensions
        logger.info("Checking existing table schema...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' AND column_name = 'embedding';
        """)
        
        existing_schema = cursor.fetchone()
        if existing_schema:
            logger.info("Table exists, checking vector dimensions...")
            # If table exists with wrong dimensions, drop it
            cursor.execute("DROP TABLE IF EXISTS document_chunks CASCADE;")
            logger.info("Dropped existing table with incorrect schema.")
        
        # Create document_chunks table with correct dimensions
        logger.info("Creating document_chunks table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id UUID PRIMARY KEY,
                source_document VARCHAR(255) NOT NULL,
                entity VARCHAR(100),
                language VARCHAR(5),
                document_type VARCHAR(100) NOT NULL,
                main_section_title TEXT,
                sub_section_title TEXT,
                text_content TEXT NOT NULL,
                summary TEXT,
                generated_labels TEXT[],
                embedding VECTOR(1024)
            );
        """)
        
        # Create index for efficient similarity searches
        logger.info("Creating vector index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
            ON document_chunks USING ivfflat (embedding vector_l2_ops) 
            WITH (lists = 100);
        """)
        
        conn.commit()
        logger.info("Database setup completed successfully.")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def insert_chunk(conn, chunk: Dict[str, Any]) -> None:
    """Insert a processed chunk into the database."""
    cursor = conn.cursor()
    
    try:
        # Convert embedding to list for psycopg2
        embedding_list = chunk['embedding'].tolist() if isinstance(chunk['embedding'], np.ndarray) else chunk['embedding']
        
        cursor.execute("""
            INSERT INTO document_chunks (
                chunk_id, source_document, entity, language, document_type,
                main_section_title, sub_section_title, text_content, 
                summary, generated_labels, embedding
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            chunk['chunk_id'],
            chunk['source_document'],
            chunk['entity'],
            chunk['language'],
            chunk['document_type'],
            chunk['main_section_title'],
            chunk['sub_section_title'],
            chunk['raw_text'],  # Sadece gerçek metin içeriği
            chunk['summary'],
            chunk['generated_labels'],
            embedding_list
        ))
        
        conn.commit()
        logger.info(f"Successfully inserted chunk {chunk['chunk_id']}")
        
    except Exception as e:
        logger.error(f"Error inserting chunk {chunk['chunk_id']}: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def run_pipeline() -> None:
    """Main pipeline function."""
    logger.info("Starting RAG Pipeline...")
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'bankbot'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'), # Değişiklik burada yapıldı
        'port': os.getenv('DB_PORT', '5432')
    }
    
    conn = None
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(**db_params)
        
        # Setup database schema
        setup_database(conn)
        
        # Initialize embedding model with GPU support
        logger.info("Loading embedding model...")
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device for embeddings: {device}")
        embedding_model = SentenceTransformer('intfloat/multilingual-e5-large', device=device)
        
        # Initialize Yi-1.5-9B-Chat model
        logger.info("Loading Yi-1.5-9B-Chat model...")
        model_path = os.getenv('YI_MODEL_PATH', './models/yi-1.5-9b-chat/Yi-1.5-9B-Chat-Q4_K_M.gguf')
        llm = AutoModelForCausalLM.from_pretrained(
            model_path,
            model_type="llama",  # Yi gguf is llama-compatible
            gpu_layers=50,
            context_length=8192,
            max_new_tokens=1024,
            temperature=0.2,
            threads=8
        )
        
        # Parse documents
        logger.info("Parsing documents...")
        
        # Parse TEB document
        teb_chunks = parse_document(
            content=TEB_DOCUMENT_CONTENT,
            source_document="aydinlatmametni.pdf",
            entity="TEB",
            language="tr",
            document_type="Public Product Info"
        )
        
        # Parse BNP Paribas document
        bnp_chunks = parse_document(
            content=BNP_PARIBAS_DOCUMENT_CONTENT,
            source_document="BNP_Paribas_Cardif_Privacy_Notice.txt",
            entity="BNP Paribas Cardif",
            language="fr",
            document_type="Public Product Info"
        )
        
        # Parse Basel III document
        basel_chunks = parse_document(
            content=BASEL_III_DOCUMENT_CONTENT,
            source_document="Sorularla_Basel_III_BDDK_Aralik_2010.pdf",
            entity="BDDK",
            language="tr",
            document_type="Regulatory Docs"
        )
        
        # Parse Bank of America document
        boa_chunks = parse_document(
            content=BOA_DOCUMENT_CONTENT,
            source_document="bankofamer.txt",
            entity="Bank of America",
            language="en",
            document_type="Public Product Info"
        )
        
        # Combine all chunks
        all_chunks = teb_chunks + bnp_chunks + basel_chunks + boa_chunks
        total_chunks = len(all_chunks)
        
        logger.info(f"Total chunks to process: {total_chunks}")
        
        # Process each chunk
        for i, chunk in enumerate(all_chunks):
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing chunk {i+1}/{total_chunks}")
            logger.info(f"{'='*80}")
            logger.info(f"📄 Source Document: {chunk['source_document']}")
            logger.info(f"🏢 Entity: {chunk['entity']}")
            logger.info(f"🌐 Language: {chunk['language']}")
            logger.info(f"📋 Document Type: {chunk['document_type']}")
            logger.info(f"📖 Main Section: {chunk['main_section_title']}")
            logger.info(f"📝 Sub Section: {chunk['sub_section_title']}")
            logger.info(f"📊 Chunk ID: {chunk['chunk_id']}")
            logger.info(f"📄 Text Content (first 500 chars): {chunk['raw_text'][:500]}...")
            logger.info(f"📊 Full Text Length: {len(chunk['raw_text'])} characters")
            
            # Generate summary using Yi-1.5-9B-Chat
            logger.info("🧠 Generating summary with Yi-1.5-9B-Chat...")
            chunk['summary'] = get_summary_from_yi(llm, chunk['raw_text'])
            logger.info(f"📋 Generated Summary: {chunk['summary']}")
            
            # Generate labels using Yi-1.5-9B-Chat
            logger.info("🏷️ Generating labels with Yi-1.5-9B-Chat...")
            chunk['generated_labels'] = get_labels_from_yi(llm, chunk['raw_text'])
            logger.info(f"🏷️ Generated Labels [4 tags]: {chunk['generated_labels']}")
            
            # Generate embedding
            logger.info("🔢 Generating embedding...")
            chunk['embedding'] = embedding_model.encode(chunk['raw_text'])
            logger.info(f"🔢 Embedding Shape: {chunk['embedding'].shape}")
            logger.info(f"🔢 Embedding Dimensions: {len(chunk['embedding'])}")
            
            # Insert into database
            logger.info("💾 Inserting chunk into database...")
            insert_chunk(conn, chunk)
            logger.info("✅ Chunk successfully processed and stored!")
            logger.info(f"{'='*80}\n")
        
        logger.info(f"Pipeline complete. All {total_chunks} chunks have been processed and stored in the database.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user.")
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        exit(1) 