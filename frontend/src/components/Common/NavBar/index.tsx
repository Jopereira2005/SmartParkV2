"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

import styled from "./style.module.scss";

import { HomeIcon } from "@/assets/Common/Home";
import { MarkIcon } from "@/assets/Common/Mark";
import { ProfileIcon } from "@/assets/Common/Profile";
import { SearchIcon } from "@/assets/Common/Search";

import { logout } from "@/lib/auth/logout";


export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav className={ styled.navbar }>
      <Link href="/search" className={ `${styled.navbar__item} ${pathname == "/search" ? styled.navbar__item_active : ''}` }>
        <SearchIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Busca</h1>
      </Link>
      <Link href="/" className={ `${styled.navbar__item} ${pathname == "/" ? styled.navbar__item_active : ''}` }>
        <HomeIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Início</h1>
      </Link>
      <div onClick={logout} className={ `${styled.navbar__item} ${pathname == "/saved" ? styled.navbar__item_active : ''}` }>
        <MarkIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Salvos</h1>
      </div>
      <Link href="/profile" className={ `${styled.navbar__item} ${pathname == "/profile" ? styled.navbar__item_active : ''}` }>
        <ProfileIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Perfil</h1>
      </Link>
    </nav>
  );
};