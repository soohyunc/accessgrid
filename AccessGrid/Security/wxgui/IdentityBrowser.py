import time

from wxPython.wx import *

from AccessGrid.Security.Utilities import GetCNFromX509Subject

from CertificateBrowserBase import CertificateBrowserBase
from CertificateViewer import CertificateViewer

import CertificateManagerWXGUI
#from CertificateManagerWXGUI import ImportPKCS12IdentityCertificate
#from CertificateManagerWXGUI import ImportPEMIdentityCertificate
#from CertificateManagerWXGUI import ExportIDCertDialog

from ImportIdentityCertDialog import ImportIdentityCertDialog

class IdentityBrowser(CertificateBrowserBase):
    def __init__(self, parent, id, certMgr):
        CertificateBrowserBase.__init__(self, parent, id, certMgr)

    def _buildButtons(self, sizer):

        #
        # Buttons that are only valid when a cert is selected.
        #
        self.certOnlyButtons = []

        b = wxButton(self, -1, "Import")
        EVT_BUTTON(self, b.GetId(), self.OnImport)
        sizer.Add(b, 0, wxEXPAND)

        b = wxButton(self, -1, "Export")
        EVT_BUTTON(self, b.GetId(), self.OnExport)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Delete")
        EVT_BUTTON(self, b.GetId(), self.OnDelete)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        b = wxButton(self, -1, "Set as default")
        EVT_BUTTON(self, b.GetId(), self.OnSetDefault)
        sizer.Add(b, 0, wxEXPAND)
        self.defaultButton = b
        b.Enable(0)

        b = wxButton(self, -1, "View certificate")
        EVT_BUTTON(self, b.GetId(), self.OnViewCertificate)
        sizer.Add(b, 0, wxEXPAND)
        self.certOnlyButtons.append(b)

        for b in self.certOnlyButtons:
            b.Enable(0)

    def OnImport(self, event):
        """
        Import a new identity certificate.
        """

        dlg = ImportIdentityCertDialog(self, self.certMgr)
        ret = dlg.Run()
        dlg.Destroy()

        if ret is None:
            return

        certType, certFile, privateKeyFile = ret

        if certType == "PKCS12":
            impCert = CertificateManagerWXGUI.ImportPKCS12IdentityCertificate(self.certMgr, certFile)
        elif certType == "PEM":
            impCert = CertificateManagerWXGUI.ImportPEMIdentityCertificate(self.certMgr, certFile, privateKeyFile)
        else:

            dlg = wxMessageDialog(self,
                                  "Unknown certificate type in import."
                                  "Import failed",
                                  style = wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            return

        #
        # TODO : bring up confirmation dialog?
        #

        self.Load()

    def OnExport(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = CertificateManagerWXGUI.ExportIDCertDialog(self, cert)
        dlg.ShowModal()
        dlg.Destroy()

    def OnDelete(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return


        dlg = wxMessageDialog(self,
                              "Deleting a certificate is an irreversible operation.\n" +
                              "Really delete certificate for identity " +
                              cert.GetShortSubject() + "?",
                              "Really delete?",
                              style = wxYES_NO | wxNO_DEFAULT)
        ret = dlg.ShowModal()
        dlg.Destroy()

        if ret == wxID_NO:
            return

        self.certMgr.GetCertificateRepository().RemoveCertificate(cert)
        self.certMgr.GetUserInterface().InitGlobusEnvironment()
        self.Load()

    def OnSetDefault(self, event):
        pass

    def OnCertSelected(self, event, cert):
        if cert is None:
            return

        for b in self.certOnlyButtons:
            b.Enable(1)

        if self.certMgr.IsDefaultIdentityCert(cert):
            self.defaultButton.Enable(0)
        else:
            self.defaultButton.Enable(1)

    def OnCertActivated(self, event, cert):
        if cert is None:
            return

        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    def OnViewCertificate(self, event):
        cert = self.GetSelectedCertificate()
        if cert is None:
            return

        dlg = CertificateViewer(self, -1, cert, self.certMgr)
        dlg.Show()

    #
    # Overrides from superclass.
    #

    def _LoadCerts(self):
        return self.certMgr.GetIdentityCerts()

    def _FormatCert(self, cert):
        subj = GetCNFromX509Subject(cert.GetSubject())
        issuer = GetCNFromX509Subject(cert.GetIssuer())

        proxyValid = ""

        if self.certMgr.IsDefaultIdentityCert(cert):
            isDefault= "Y"

            #
            # If this is the default identity cert,
            # we might have a proxy. Note that in future
            # when we may have multiple valid proxies, this
            # test will have to move out of here. It's here
            # as a currently-valid optimization.
            #

            proxyValid = self._TestGlobusProxy(cert)
            
        else:
            isDefault = ""

        valid = self.certMgr.CheckValidity(cert)

        return cert, [subj, issuer, isDefault, valid, proxyValid]

    def _TestGlobusProxy(self, defaultCert):

        try:
            proxyCert = self.certMgr.GetGlobusProxyCert()

        except:
            return "Missing"

        if not proxyCert.IsGlobusProxy():
            return "Not a proxy"

        proxyIssuer = proxyCert.GetIssuer()
        idSubject = defaultCert.GetSubject()
        if proxyIssuer.get_der() != idSubject.get_der():
            return "Proxy for other id"

        #
        # Check to see if the proxy cert has expired.
        #

        if proxyCert.IsExpired():
            return "Expired"

        if not self.certMgr.VerifyCertificatePath(proxyCert):
            return "Missing CA"

        #
        # Otherwise, return the remaining lifetime.
        #

        left = proxyCert.GetNotValidAfter() - int(time.time())

        out = ""
        if left > 86400:
            days = int(left / 86400)
            out += "%dd " % (days)

            left = left % 86400

        hour = int(left / 3600)
        left = left % 3600

        min = int(left / 60)
        sec = left % 60

        out += "%02d:%02d:%02d left" % (hour, min, sec)

        return out

    def _getListColumns(self):
        return ["Name", "Issuer", "Default", "Validity", "Proxy status"]

    def _getListColumnWidths(self):
        return [wxLIST_AUTOSIZE, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER, wxLIST_AUTOSIZE, wxLIST_AUTOSIZE_USEHEADER]

