%global _hardened_build 1

Name:                  ntp
Version:               4.2.8p15
Release:               6
Summary:               A protocol designed to synchronize the clocks of computers over a network
License:               MIT and BSD and BSD with advertising
URL:                   https://www.ntp.org/
Source0:               https://www.eecis.udel.edu/~ntp/ntp_spool/ntp4/ntp-4.2/ntp-%{version}.tar.gz
Source1:               ntp.conf
Source2:               ntp.keys
Source4:               ntpd.sysconfig
Source6:               ntp.step-tickers
Source7:               ntpdate.wrapper
Source8:               ntp.cryptopw
Source9:               ntpdate.sysconfig
Source10:              ntp.dhclient
Source12:              ntpd.service
Source13:              ntpdate.service
Source14:              ntp-wait.service
Source15:              sntp.service
Source16:              sntp.sysconfig
Patch1:                ntp-ssl-libs.patch
Patch2:                bugfix-fix-bind-port-in-debug-mode.patch
Patch3:                bugfix-fix-ifindex-length.patch
Patch4:                fix-multiple-defination-with-gcc-10.patch
Patch5:                Do-not-use-PTHREAD_STACK_MIN-on-glibc.patch
Patch6:                fix-MD5-manpage.patch

BuildRequires:	       libcap-devel openssl-devel libedit-devel libevent-devel pps-tools-devel
BuildRequires:         autogen autogen-libopts-devel systemd gcc perl-generators perl-HTML-Parser
Requires(pre):         shadow-utils autogen >= 5.18.16
%{?systemd_requires}
Recommends:            ntpstat timedatex
Provides:              ntpdate sntp
Obsoletes:             ntpdate sntp

%description
NTP is a protocol designed to synchronize the clocks of computers over a network, \
NTP version 4, a significant revision of the previous NTP standard, is the current \
development version. It is formalized by RFCs released by the IETF.

%package perl
Summary: NTP utilities present with Perl
Requires: %{name} = %{version}-%{release}
%{?systemd_requires}
BuildArch: noarch

%description perl
Provides Perl scripts calc_tickadj, ntp-wait and ntptrace.

%package_help

%global ntpdocdir %{?_pkgdocdir}%{!?_pkgdocdir:%{_docdir}/%{name}-%{version}}

%if 0%{!?vendorzone:1}
%global vendorzone %(source /etc/os-release && echo ${ID}.)
%endif

%prep
%autosetup -n %{name}-%{version} -p1

sed -i 's|\r||g' html/scripts/{footer.txt,style.css}
for f in COPYRIGHT; do
        iconv -f iso8859-1 -t utf8 -o ${f}{_,} && touch -r ${f}{,_} && mv -f ${f}{_,}
done

%build
sed -i 's|$CFLAGS -Wstrict-overflow|$CFLAGS|' configure sntp/configure
export CFLAGS="$RPM_OPT_FLAGS -fno-strict-aliasing -fno-strict-overflow"
%configure \
        --sysconfdir=%{_sysconfdir}/ntp/crypto --with-locfile=redhat \
        --without-ntpsnmpd --enable-all-clocks --enable-parse-clocks \
        --enable-ntp-signd=%{_localstatedir}/run/ntp_signd --disable-local-libopts

sed -i 's|/var/db/ntp-kod|%{_localstatedir}/lib/sntp/kod|' sntp/sntp{-opts.c,.1*}
sed -i 's|/etc/ntp/drift|%{_localstatedir}/lib/ntp/drift|' \
        scripts/calc_tickadj/calc_tickadj{,.m*.in}
echo '#define KEYFILE "%{_sysconfdir}/ntp/keys"' >> ntpdate/ntpdate.h
echo '#define NTP_VAR "%{_localstatedir}/log/ntpstats/"' >> config.h

%make_build

sed -e 's|@PATH_PERL@|%{_bindir}/perl|' -e 's|@[^@]*_MS@|8|g' \
        < scripts/deprecated/html2man.in \
        > scripts/deprecated/html2man
pushd html
perl ../scripts/deprecated/html2man
sed -i 's/^[\t\ ]*$//;/./,/^$/!d' man/man*/*.[58]
popd

%install
%make_install

cp -r html/man/man8/{ntpdate,ntptime,tickadj}* $RPM_BUILD_ROOT%{_mandir}/man8

rm -rf $RPM_BUILD_ROOT%{_docdir}
install -d $RPM_BUILD_ROOT%{ntpdocdir}
cp -p ChangeLog NEWS $RPM_BUILD_ROOT%{ntpdocdir}

find html | grep -E '\.(html|css|txt|jpg|gif)$' | grep -v '/build/\|sntp' | \
        cpio -pmd $RPM_BUILD_ROOT%{ntpdocdir}
find $RPM_BUILD_ROOT%{ntpdocdir} -type f | xargs chmod 644
find $RPM_BUILD_ROOT%{ntpdocdir} -type d | xargs chmod 755

pushd $RPM_BUILD_ROOT
install -d .%{_sysconfdir}/{ntp/crypto,sysconfig,dhcp/dhclient.d} .%{_libexecdir}
install -d .%{_localstatedir}/{lib/{s,}ntp,log/ntpstats} .%{_unitdir}
touch .%{_localstatedir}/lib/{ntp/drift,sntp/kod}
sed -e 's|VENDORZONE\.|%{vendorzone}|' \
        -e 's|ETCNTP|%{_sysconfdir}/ntp|' \
        -e 's|VARNTP|%{_localstatedir}/lib/ntp|' \
        < %{SOURCE1} > .%{_sysconfdir}/ntp.conf
touch -r %{SOURCE1} .%{_sysconfdir}/ntp.conf
install -p -m600 %{SOURCE2} .%{_sysconfdir}/ntp/keys
install -p -m755 %{SOURCE7} .%{_libexecdir}/ntpdate-wrapper
install -p -m644 %{SOURCE4} .%{_sysconfdir}/sysconfig/ntpd
install -p -m644 %{SOURCE9} .%{_sysconfdir}/sysconfig/ntpdate
sed -e 's|VENDORZONE\.|%{vendorzone}|' \
        < %{SOURCE6} > .%{_sysconfdir}/ntp/step-tickers
touch -r %{SOURCE6} .%{_sysconfdir}/ntp/step-tickers
sed -e 's|VENDORZONE\.|%{vendorzone}|' \
        < %{SOURCE16} > .%{_sysconfdir}/sysconfig/sntp
touch -r %{SOURCE16} .%{_sysconfdir}/sysconfig/sntp
install -p -m600 %{SOURCE8} .%{_sysconfdir}/ntp/crypto/pw
install -p -m755 %{SOURCE10} .%{_sysconfdir}/dhcp/dhclient.d/ntp.sh
install -p -m644 %{SOURCE12} .%{_unitdir}/ntpd.service
install -p -m644 %{SOURCE13} .%{_unitdir}/ntpdate.service
install -p -m644 %{SOURCE14} .%{_unitdir}/ntp-wait.service
install -p -m644 %{SOURCE15} .%{_unitdir}/sntp.service

mkdir .%{_prefix}/lib/systemd/ntp-units.d
echo 'ntpd.service' > .%{_prefix}/lib/systemd/ntp-units.d/60-ntpd.list

popd

%check
make check

%pre
/usr/sbin/groupadd -g 38 ntp  2> /dev/null || :
/usr/sbin/useradd -u 38 -g 38 -s /sbin/nologin -M -r -d %{_sysconfdir}/ntp ntp 2>/dev/null || :

%post
%systemd_post ntpd.service ntpdate.service sntp.service

%post perl
%systemd_post ntp-wait.service

%preun
%systemd_preun ntpd.service ntpdate.service sntp.service

%preun perl
%systemd_preun ntp-wait.service

%postun
%systemd_postun_with_restart ntpd.service ntpdate.service sntp.service

%postun perl
%systemd_postun ntp-wait.service

%files
%defattr(-,root,root)
%doc COPYRIGHT ChangeLog NEWS
%license COPYRIGHT
%dir %attr(-,ntp,ntp) %{_localstatedir}/lib/ntp
%dir %attr(-,ntp,ntp) %{_localstatedir}/log/ntpstats
%dir %{_localstatedir}/lib/sntp
%dir %{_sysconfdir}/ntp
%dir %attr(750,root,ntp) %{_sysconfdir}/ntp/crypto
%dir %{_sysconfdir}/dhcp/dhclient.d
%config(noreplace) %{_sysconfdir}/sysconfig/ntpd
%config(noreplace) %verify(not md5 size mtime) %{_sysconfdir}/ntp.conf
%config(noreplace) %{_sysconfdir}/sysconfig/ntpdate
%config(noreplace) %verify(not md5 size mtime) %{_sysconfdir}/ntp/step-tickers
%config(noreplace) %{_sysconfdir}/ntp/keys
%config(noreplace) %{_sysconfdir}/ntp/crypto/pw
%config(noreplace) %{_sysconfdir}/sysconfig/sntp
%{_sysconfdir}/dhcp/dhclient.d/ntp.sh
%{_sbindir}/ntp-keygen
%{_sbindir}/ntpd
%{_sbindir}/ntpdc
%{_sbindir}/ntpq
%{_sbindir}/ntptime
%{_sbindir}/tickadj
%{_sbindir}/ntpdate
%{_sbindir}/sntp
%ghost %attr(644,ntp,ntp) %{_localstatedir}/lib/ntp/drift
%ghost %{_localstatedir}/lib/sntp/kod

%{_unitdir}/*.service
%{_prefix}/lib/systemd/ntp-units.d/*.list
%{_libexecdir}/ntpdate-wrapper

%files perl
%defattr(-,root,root)
%{_sbindir}/calc_tickadj
%{_sbindir}/ntp-wait
%{_sbindir}/ntptrace
%{_unitdir}/ntp-wait.service
%{_datadir}/ntp

%files help
%defattr(-,root,root)
%dir %{ntpdocdir}
%{ntpdocdir}/html
%{_mandir}/man5/*.5*
%{_mandir}/man8/*.8*

%changelog
* Fri Dec 3 2021 renmingshuai<renmingshuai@huawei.com> - 4.2.8p15-6
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: add conflict with chronyd.service in ntpd.service

* Wed Dec 1 2021 renmingshuai<renmingshuai@huawei.com> - 4.2.8p15-5
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: fix-MD5-manpage

* Tue Aug 10 2021 renmingshuai<renmingshuai@huawei.com> - 4.2.8p15-4
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: do not use PTHREAD_STACK_MIN on glibc

* Fri Jul 30 2021 renmingshuai<renmingshuai@huawei.com> - 4.2.8p15-3
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: fix multiple defination with gcc 10

* Tue Sep 01 2020 yuboyun<yuboyun@huawei.com> - 4.2.8p15-2
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: fix ntpd service start failure

* Fri Jul 24 2020 yuboyun<yuboyun@huawei.com> - 4.2.8p15-1
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: update to 4.2.8p15

* Tue Jun 30 2020 yuboyun<yuboyun@huawei.com> - 4.2.8p14-1
- Type:bugfix
- ID:NA
- SUG:NA
- DESC: update to 4.2.8p14

* Tue Apr 14 2020 wangli<wangli221@huawei.com> - 4.2.8p13-6
- Type:security
- ID:NA
- SUG:NA
- DESC: solve fuzz test problem 

* Thu Mar 12 2020 openEuler Buildteam <buildteam@openeuler.org> - 4.2.8p13-5
- Type:bugfix
- Id:NA
- SUG:NA
- DESC:enable developer use cases

* Sat Jan 18 2020 openEuler Buildteam <buildteam@openeuler.org> - 4.2.8p13-4
- Type:enhancement
- Id:NA
- SUG:NA
- DESC:modify the ntp.conf

* Mon Oct 21 2019 openEuler Buildteam <buildteam@openeuler.org> - 4.2.8p13-3
- Type:enhancement
- Id:NA
- SUG:NA
- DESC:modify the location of COPYRIGHT

* Mon Oct 14 2019 openEuler Buildteam <buildteam@openeuler.org> - 4.2.8p13-2
- Type:enhancement
- Id:NA
- SUG:NA
- DESC:Modify error changelog information

* Mon Sep 16 2019 openEuler Buildteam <buildteam@openeuler.org> - 4.2.8p13-1
- Type:enhancement
- Id:NA
- SUG:NA
- DESC:Fix building without zlib-devel

* Tue Sep 3 2019 liyongqiang<liyongqiang10@huawei.com> - 4.2.8p12-2
- Package init    
