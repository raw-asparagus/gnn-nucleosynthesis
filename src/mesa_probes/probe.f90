! mesa_probe — read-only introspection driver for MESA r23.05.1 nets.
!
! Usage:  mesa_probe <mode> <net_file> <out_csv> [screening_mode]
!   dump_net     — one row per net reaction: name, participants w/ stoichiometry,
!                  source attribution (reaclib fwd / detailed-balance reverse /
!                  weaklib pair id), category, Q, Qneu.
!   dump_inverse — one row per detailed-balance reverse rate: chapter, Ni, No,
!                  inverse_coefficients, inverse_exp (Appendix-B screen).
!   eval_rates   — stdin: one T9 per line. Raw (unscreened) rate per reaction × T9.
!   eval_weak    — stdin: "T9 rho ye" per line. Weaklib lambda per weak reaction
!                  (eta=0: plain weaklib lambda depends only on (T9, lYeRho);
!                  special weak rates are OFF, matching bbq/training defaults),
!                  plus the raw reaclib rate for the same reaction id.
!   eval_screen  — stdin: "T9 rho ye" per line. Net-equivalent screening factor
!                  per reaction (pair or two-stage triple, mirroring
!                  net/private/net_screen.f90) on an ni56/fe58 mix with the
!                  requested ye. screening_mode arg default 'chugunov'
!                  (bbq default = training-label config).
!
! MESA sources are never modified; the rate cache writes go to the standard
! MESA cache locations (same as any bbq run).
program mesa_probe
   use utils_lib, only: mesa_error
   use math_lib
   use const_lib, only: const_init
   use chem_def, only: chem_isos, num_chem_isos, category_name, num_categories
   use chem_lib, only: chem_init, basic_composition_info
   use rates_lib
   use rates_def
   use net_lib
   use net_def, only: Net_General_Info

   implicit none

   character (len=256) :: mode, net_file, out_csv, screen_mode_str
   integer :: ierr, handle, species, num_reactions, out_unit
   integer, pointer :: chem_id(:), net_iso(:), reaction_id(:)
   type (Net_General_Info), pointer :: g

   ierr = 0
   if (command_argument_count() < 3) then
      write(*,*) 'usage: mesa_probe <mode> <net_file> <out_csv> [screening_mode]'
      call mesa_error(__FILE__,__LINE__)
   end if
   call get_command_argument(1, mode)
   call get_command_argument(2, net_file)
   call get_command_argument(3, out_csv)
   screen_mode_str = 'chugunov'
   if (command_argument_count() >= 4) call get_command_argument(4, screen_mode_str)

   call initialize(ierr)
   if (ierr /= 0) call mesa_error(__FILE__,__LINE__)

   call setup_net(net_file, ierr)
   if (ierr /= 0) call mesa_error(__FILE__,__LINE__)

   open(newunit=out_unit, file=trim(out_csv), action='write', status='replace')

   select case (trim(mode))
   case ('dump_net')
      call do_dump_net()
   case ('dump_inverse')
      call do_dump_inverse()
   case ('eval_rates')
      call do_eval_rates()
   case ('eval_weak')
      call do_eval_weak()
   case ('eval_screen')
      call do_eval_screen()
   case default
      write(*,*) 'unknown mode: ' // trim(mode)
      call mesa_error(__FILE__,__LINE__)
   end select

   close(out_unit)

contains

   subroutine initialize(ierr)
      integer, intent(out) :: ierr
      ierr = 0
      call math_init()
      call const_init('', ierr)   ! '' -> use $MESA_DIR
      if (ierr /= 0) return
      call chem_init('isotopes.data', ierr)
      if (ierr /= 0) return
      ! same arguments bbq passes with an empty &nuclear namelist
      ! (training-label configuration): default reaclib, no suzuki,
      ! no special weak rates.
      call rates_init('reactions.list', '', 'rate_tables', .false., .false., &
                      '', '', '', ierr)
      if (ierr /= 0) return
      call rates_warning_init(.false., 10d0)
      call net_init(ierr)
   end subroutine initialize

   subroutine setup_net(net_file, ierr)
      character (len=*), intent(in) :: net_file
      integer, intent(out) :: ierr
      ierr = 0
      handle = alloc_net_handle(ierr)
      if (ierr /= 0) return
      call net_start_def(handle, ierr)
      if (ierr /= 0) return
      call read_net_file(net_file, handle, ierr)
      if (ierr /= 0) return
      call net_finish_def(handle, ierr)
      if (ierr /= 0) return
      call net_ptr(handle, g, ierr)
      if (ierr /= 0) return
      species = g% num_isos
      num_reactions = g% num_reactions
      allocate(chem_id(species), net_iso(num_chem_isos), reaction_id(num_reactions))
      call get_chem_id_table(handle, species, chem_id, ierr)
      if (ierr /= 0) return
      call get_net_iso_table(handle, net_iso, ierr)
      if (ierr /= 0) return
      call get_reaction_id_table(handle, num_reactions, reaction_id, ierr)
      if (ierr /= 0) return
      call net_setup_tables(handle, '', ierr)
   end subroutine setup_net

   function participants_str(pairs, maxn, ir) result(s)
      ! encode "(coeff)name;(coeff)name" from a reaction_inputs/outputs column
      integer, pointer, intent(in) :: pairs(:,:)
      integer, intent(in) :: maxn, ir
      character (len=128) :: s
      integer :: j, cf, cid
      character (len=16) :: buf
      s = ''
      do j = 1, maxn
         cf = pairs(2*j-1, ir)
         if (cf == 0) exit
         cid = pairs(2*j, ir)
         write(buf,'(i0)') cf
         if (j > 1) s = trim(s) // ';'
         s = trim(s) // trim(buf) // ':' // trim(chem_isos% name(cid))
      end do
   end function participants_str

   subroutine do_dump_net()
      integer :: i, ir, idxf, idxr, wid, cat, cid_in, cid_out
      character (len=128) :: ins, outs
      character (len=32) :: lhs, rhs, catname
      write(out_unit,'(a)') 'i,name,category,q,qneu,is_weak,weaklib_id,' // &
         'weak_lhs,weak_rhs,reaclib_fwd_idx,reaclib_rev_idx,inputs,outputs'
      do i = 1, num_reactions
         ir = reaction_id(i)
         idxf = reaclib_index(reaction_Name(ir))
         idxr = reaclib_reverse(reaction_Name(ir))
         wid = 0
         lhs = ''
         rhs = ''
         cid_in = weak_reaction_info(1,ir)
         cid_out = weak_reaction_info(2,ir)
         if (cid_in > 0 .and. cid_out > 0) then
            lhs = chem_isos% name(cid_in)
            rhs = chem_isos% name(cid_out)
            wid = get_weak_rate_id(lhs, rhs)
         end if
         cat = reaction_categories(ir)
         catname = ''
         if (cat >= 1 .and. cat <= num_categories) catname = category_name(cat)
         ins = participants_str(reaction_inputs, max_num_reaction_inputs, ir)
         outs = participants_str(reaction_outputs, max_num_reaction_outputs, ir)
         write(out_unit,'(i0,a,es23.15e3,a,es23.15e3,a,i0,a,i0,a,i0,a)') &
            i, ','//trim(reaction_Name(ir))//','//trim(catname)//',', &
            std_reaction_Qs(ir), ',', std_reaction_neuQs(ir), &
            ','//merge('1','0',is_weak_reaction(ir))//',', wid, &
            ','//trim(lhs)//','//trim(rhs)//',', idxf, ',', idxr, &
            ','//trim(ins)//','//trim(outs)
      end do
   end subroutine do_dump_net

   subroutine do_dump_inverse()
      integer :: i, ir, idxr, ch
      write(out_unit,'(a)') 'i,name,reaclib_idx,fwd_handle,rev_handle,' // &
         'chapter,n_in,n_out,inv_coeff_1,inv_coeff_2,inv_exp,reaclib_q'
      do i = 1, num_reactions
         ir = reaction_id(i)
         idxr = reaclib_reverse(reaction_Name(ir))
         if (idxr <= 0) cycle
         ch = reaclib_rates% chapter(idxr)
         write(out_unit,'(i0,a,i0,a,i0,a,i0,a,i0,a,es23.15e3,a,es23.15e3,a,i0,a,es23.15e3)') &
            i, ','//trim(reaction_Name(ir))//',', idxr, &
            ','//trim(reaclib_rates% reaction_handle(idxr))// &
            ','//trim(reaclib_rates% reverse_handle(idxr))//',', &
            ch, ',', Nin(ch), ',', Nout(ch), ',', &
            reaclib_rates% inverse_coefficients(1,idxr), ',', &
            reaclib_rates% inverse_coefficients(2,idxr), ',', &
            reaclib_rates% inverse_exp(idxr), ',', reaclib_rates% Q(idxr)
      end do
   end subroutine do_dump_inverse

   subroutine do_eval_rates()
      type (T_Factors), pointer :: tf
      real(dp) :: t9, temp, raw
      integer :: i, ir, ios, jerr
      character (len=256) :: line
      allocate(tf)
      write(out_unit,'(a)') 't9,i,name,raw_rate,ierr'
      do
         read(*,'(a)',iostat=ios) line
         if (ios /= 0) exit
         if (len_trim(line) == 0) cycle
         read(line,*) t9
         temp = t9*1d9
         call eval_tfactors(tf, log10(temp), temp)
         do i = 1, num_reactions
            ir = reaction_id(i)
            jerr = 0
            raw = 0d0
            call get_raw_rate(ir, temp, tf, raw, jerr)
            write(out_unit,'(es13.6e2,a,i0,a,es23.15e3,a,i0)') &
               t9, ',', i, ','//trim(reaction_Name(ir))//',', raw, ',', jerr
         end do
      end do
   end subroutine do_eval_rates

   subroutine do_eval_weak()
      type (T_Factors), pointer :: tf
      type (Coulomb_Info), pointer :: cc
      real(dp) :: t9, rho, ye, temp, yerho, raw
      integer :: i, k, nw, ios, jerr
      character (len=256) :: line
      integer, allocatable :: ids(:), rids(:), rownum(:)
      real(dp), allocatable, dimension(:) :: lambda, dl_dlnT, dl_dlnRho, &
         q, dq_dlnT, dq_dlnRho, qneu, dqneu_dlnT, dqneu_dlnRho
      character (len=8), allocatable :: lhs(:), rhs(:)

      allocate(tf)
      nullify(cc)   ! unused: do_ecapture=.false. (no special weak rates)

      ! collect the net's weak reactions that have a (lhs, rhs) nuclide pair
      nw = 0
      do i = 1, num_reactions
         if (weak_reaction_info(1,reaction_id(i)) > 0 .and. &
             weak_reaction_info(2,reaction_id(i)) > 0) nw = nw + 1
      end do
      allocate(ids(nw), rids(nw), rownum(nw), lhs(nw), rhs(nw), &
         lambda(nw), dl_dlnT(nw), dl_dlnRho(nw), q(nw), dq_dlnT(nw), &
         dq_dlnRho(nw), qneu(nw), dqneu_dlnT(nw), dqneu_dlnRho(nw))
      k = 0
      do i = 1, num_reactions
         if (weak_reaction_info(1,reaction_id(i)) <= 0 .or. &
             weak_reaction_info(2,reaction_id(i)) <= 0) cycle
         k = k + 1
         rownum(k) = i
         rids(k) = reaction_id(i)
         lhs(k) = chem_isos% name(weak_reaction_info(1,rids(k)))
         rhs(k) = chem_isos% name(weak_reaction_info(2,rids(k)))
         ids(k) = get_weak_rate_id(lhs(k), rhs(k))
      end do

      write(out_unit,'(a)') 't9,rho,ye,i,name,lhs,rhs,weaklib_id,' // &
         'lambda_weaklib,q,qneu,raw_reaclib_rate,ierr'
      do
         read(*,'(a)',iostat=ios) line
         if (ios /= 0) exit
         if (len_trim(line) == 0) cycle
         read(line,*) t9, rho, ye
         temp = t9*1d9
         yerho = ye*rho
         lambda = 0d0; dl_dlnT = 0d0; dl_dlnRho = 0d0
         q = 0d0; dq_dlnT = 0d0; dq_dlnRho = 0d0
         qneu = 0d0; dqneu_dlnT = 0d0; dqneu_dlnRho = 0d0
         jerr = 0
         call eval_weak_reaction_info( &
            nw, ids, rids, cc, t9, yerho, &
            0d0, 0d0, 0d0, &
            lambda, dl_dlnT, dl_dlnRho, &
            q, dq_dlnT, dq_dlnRho, &
            qneu, dqneu_dlnT, dqneu_dlnRho, jerr)
         if (jerr /= 0) then
            write(*,*) 'eval_weak_reaction_info failed', jerr
            call mesa_error(__FILE__,__LINE__)
         end if
         call eval_tfactors(tf, log10(temp), temp)
         do k = 1, nw
            jerr = 0
            raw = 0d0
            call get_raw_rate(rids(k), temp, tf, raw, jerr)
            write(out_unit,'(es13.6e2,a,es13.6e2,a,es13.6e2,a,i0,a,i0,a,' // &
               'es23.15e3,a,es23.15e3,a,es23.15e3,a,es23.15e3,a,i0)') &
               t9, ',', rho, ',', ye, ',', rownum(k), &
               ','//trim(reaction_Name(rids(k)))//','//trim(lhs(k))// &
               ','//trim(rhs(k))//',', ids(k), ',', &
               lambda(k), ',', q(k), ',', qneu(k), ',', raw, ',', jerr
         end do
      end do
   end subroutine do_eval_weak

   subroutine do_eval_screen()
      type (Screen_Info) :: sc
      real(dp) :: t9, rho, ye, temp, logT, logRho
      real(dp) :: xh, xhe, z, abar, zbar, z2bar, z53bar, ye_actual, &
         mass_correction, sumx, x_ni, x_fe, ye1, ye2
      real(dp) :: xa(species), y(species), z158(species)
      integer :: i, ir, ios, jerr, smode, idx_ni56, idx_fe56, idx_neut
      character (len=256) :: line
      real(dp) :: scor, x_n

      smode = screening_option(trim(screen_mode_str), ierr)
      if (ierr /= 0) call mesa_error(__FILE__,__LINE__)

      idx_ni56 = 0; idx_fe56 = 0; idx_neut = 0
      do i = 1, species
         if (trim(chem_isos% name(chem_id(i))) == 'ni56') idx_ni56 = i
         if (trim(chem_isos% name(chem_id(i))) == 'fe56') idx_fe56 = i
         if (trim(chem_isos% name(chem_id(i))) == 'neut') idx_neut = i
      end do
      if (idx_ni56 == 0 .or. idx_fe56 == 0 .or. idx_neut == 0) then
         write(*,*) 'ni56/fe56/neut not all in net; cannot build ye mix'
         call mesa_error(__FILE__,__LINE__)
      end if

      write(out_unit,'(a)') 't9,rho,ye,x_ni56,x_fe56,x_neut,abar,zbar,z2bar,' // &
         'i,name,scr_iso_1,scr_iso_2,scr_iso_3,scor'
      do
         read(*,'(a)',iostat=ios) line
         if (ios /= 0) exit
         if (len_trim(line) == 0) cycle
         read(line,*) t9, rho, ye
         temp = t9*1d9
         logT = log10(temp)
         logRho = log10(rho)
         ! piecewise iron-group mix hitting the nominal ye
         ! (integer Z/A convention; mesa_80 has no iron-group isotope with
         ! Z/A < 26/56, so below that we add free neutrons)
         ye1 = 28d0/56d0   ! ni56
         ye2 = 26d0/56d0   ! fe56
         x_n = 0d0
         if (ye >= ye2) then
            x_ni = (ye - ye2)/(ye1 - ye2)
            x_fe = 1d0 - x_ni
         else
            x_ni = 0d0
            x_fe = ye/ye2
            x_n = 1d0 - x_fe
         end if
         if (x_ni < 0d0 .or. x_ni > 1d0 .or. x_fe < 0d0) then
            write(*,*) 'ye outside supported range:', ye
            call mesa_error(__FILE__,__LINE__)
         end if
         xa = 0d0
         xa(idx_ni56) = x_ni
         xa(idx_fe56) = x_fe
         xa(idx_neut) = x_n
         call basic_composition_info(species, chem_id, xa, xh, xhe, z, &
            abar, zbar, z2bar, z53bar, ye_actual, mass_correction, sumx)
         do i = 1, species
            y(i) = xa(i)/dble(chem_isos% Z_plus_N(chem_id(i)))
            z158(i) = pow(dble(chem_isos% Z(chem_id(i))), 1.58d0)
         end do
         call screen_set_context(sc, temp, rho, logT, logRho, zbar, abar, &
            z2bar, smode, species, y, z158)
         do i = 1, num_reactions
            ir = reaction_id(i)
            if (reaction_screening_info(1,ir) <= 0 .or. &
                reaction_screening_info(2,ir) <= 0) cycle
            jerr = 0
            call screen_one(sc, ir, smode, scor, jerr)
            if (jerr /= 0) cycle
            write(out_unit,'(es13.6e2,a,es13.6e2,a,es13.6e2,a,' // &
               'es13.6e2,a,es13.6e2,a,es13.6e2,a,es13.6e2,a,es13.6e2,a,' // &
               'es13.6e2,a,i0,a,es23.15e3)') &
               t9, ',', rho, ',', ye, ',', x_ni, ',', x_fe, ',', x_n, ',', &
               abar, ',', zbar, ',', z2bar, ',', i, &
               ','//trim(reaction_Name(ir))// &
               ','//trim(chem_isos% name(reaction_screening_info(1,ir)))// &
               ','//trim(chem_isos% name(reaction_screening_info(2,ir)))// &
               ','//scr3_name(ir)//',', scor
         end do
      end do
   end subroutine do_eval_screen

   function scr3_name(ir) result(s)
      integer, intent(in) :: ir
      character (len=8) :: s
      s = ''
      if (reaction_screening_info(3,ir) > 0) &
         s = chem_isos% name(reaction_screening_info(3,ir))
   end function scr3_name

   subroutine screen_one(sc, ir, smode, scor, jerr)
      ! mirrors net/private/net_screen.f90 eval_screen_pair / eval_screen_triple
      type (Screen_Info) :: sc
      integer, intent(in) :: ir, smode
      real(dp), intent(out) :: scor
      integer, intent(out) :: jerr
      integer :: i1, i2, i3, ii
      real(dp) :: a1, z1, a2, z2, a3, z3, sc1, sc2, dt, dd
      jerr = 0
      scor = 1d0
      i1 = reaction_screening_info(1,ir)
      i2 = reaction_screening_info(2,ir)
      i3 = reaction_screening_info(3,ir)
      a1 = dble(chem_isos% Z_plus_N(i1)); z1 = dble(chem_isos% Z(i1))
      a2 = dble(chem_isos% Z_plus_N(i2)); z2 = dble(chem_isos% Z(i2))
      if (i3 <= 0) then
         call pair_factor(sc, a1, z1, a2, z2, smode, scor, jerr)
         return
      end if
      a3 = dble(chem_isos% Z_plus_N(i3)); z3 = dble(chem_isos% Z(i3))
      if (z2 == 0d0) then
         if (z1 == 0d0) return   ! n + n + A: no screening
         ii = i2; i2 = i1; i1 = ii
         a1 = dble(chem_isos% Z_plus_N(i1)); z1 = dble(chem_isos% Z(i1))
         a2 = dble(chem_isos% Z_plus_N(i2)); z2 = dble(chem_isos% Z(i2))
      end if
      if (z3 == 0d0) then
         ii = i1; i1 = i3; i3 = ii
         a1 = dble(chem_isos% Z_plus_N(i1)); z1 = dble(chem_isos% Z(i1))
         a3 = dble(chem_isos% Z_plus_N(i3)); z3 = dble(chem_isos% Z(i3))
      end if
      call pair_factor(sc, a2, z2, a3, z3, smode, sc2, jerr)
      if (jerr /= 0) return
      if (z1 == 0d0) then
         scor = sc2   ! n + (A + B)
         return
      end if
      call pair_factor(sc, a1, z1, a2 + a3, z2 + z3, smode, sc1, jerr)
      if (jerr /= 0) return
      scor = sc1*sc2
   end subroutine screen_one

   subroutine pair_factor(sc, a1, z1, a2, z2, smode, scor, jerr)
      type (Screen_Info) :: sc
      real(dp), intent(in) :: a1, z1, a2, z2
      integer, intent(in) :: smode
      real(dp), intent(out) :: scor
      integer, intent(out) :: jerr
      real(dp) :: zs13, zhat, zhat2, lzav, aznut, zs13inv, dt, dd
      jerr = 0
      call screen_init_AZ_info(a1, z1, a2, z2, &
         zs13, zhat, zhat2, lzav, aznut, zs13inv, jerr)
      if (jerr /= 0) return
      call screen_pair(sc, a1, z1, a2, z2, smode, &
         zs13, zhat, zhat2, lzav, aznut, zs13inv, 0d0, &
         scor, dt, dd, jerr)
   end subroutine pair_factor

end program mesa_probe
