# New ports collection makefile for:	SWIG
# Date created:			19 April 1996
# Whom:				jkh
#
# $FreeBSD: ports/devel/swig13/Makefile,v 1.72 2006/04/04 18:06:25 pav Exp $
#

PORTNAME=	swig
PORTVERSION=	1.3.24
PORTREVISION=	2
CATEGORIES=
MASTER_SITES=	${MASTER_SITE_SOURCEFORGE} \
		http://www.vislab.uq.edu.au/ag3/freebsd/distfiles/
MASTER_SITE_SUBDIR=	${PORTNAME}

MAINTAINER=	alex@foxybanana.com
COMMENT=	Simplified Wrapper and Interface Generator

USE_AUTOTOOLS=	autoconf:253:env libtool:15

VER=		${PORTVERSION:R}
PLIST_SUB+=	PORTVERSION=${PORTVERSION}

# Supported languages: guile perl php4 python ruby tcl ocaml pike java csharp
#                      allegrocl modula3 chicken

WRKSRC=		${WRKDIR}/SWIG-1.3.24
CONFIGURE_ARGS=	--with-release-suffix=-${PORTVERSION}
CONFIGURE_ENV+=	CFLAGS="${CFLAGS} -fPIC -DPIC"
ALL_TARGET=	swig
PLIST_SUB+=	VER="${VER}"

.include <bsd.port.pre.mk>

post-patch:
	${REINPLACE_CMD} -e 's/SKIP_CHICKEN=$$/&"1"/' ${WRKSRC}/configure
	${REINPLACE_CMD} -e 's|$$RUBY |${RUBY} |' ${WRKSRC}/configure

post-configure:
	${REINPLACE_CMD} -e 's#null#&|| true#' ${WRKSRC}/Makefile

post-install:
#	${LN} -f ${PREFIX}/bin/swig ${PREFIX}/bin/swig${VER}
	${MKDIR} ${EXAMPLESDIR}/${PORTVERSION}
	cd ${WRKSRC}/Examples && ${FIND} . -type d \
		-exec ${INSTALL} -d ${EXAMPLESDIR}/${PORTVERSION}/{} \;
	cd ${WRKSRC}/Examples && ${FIND} . -type f \
		-exec ${INSTALL_DATA} {} ${EXAMPLESDIR}/${PORTVERSION}/{} \;
.if	!defined(NOPORTDOCS)
	${MKDIR} ${DOCSDIR}/${PORTVERSION}
	cd ${WRKSRC}/Doc && ${FIND} . -type d \
		-exec ${INSTALL} -d ${DOCSDIR}/${PORTVERSION}/{} \;
	cd ${WRKSRC}/Doc && ${FIND} . -type f \
		-exec ${INSTALL_DATA} {} ${DOCSDIR}/${PORTVERSION}/{} \;
.endif

.include <bsd.port.post.mk>
