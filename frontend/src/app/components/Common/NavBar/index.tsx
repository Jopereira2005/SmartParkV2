"use client";
import { useState } from "react"

import styled from "./style.module.scss";

import { HomeIcon } from "@/app/assets/Common/Home";
import { MarkIcon } from "@/app/assets/Common/Mark";
import { ProfileIcon } from "@/app/assets/Common/Profile";
import { SearchIcon } from "@/app/assets/Common/Search";

const NavBar = () => {
  // const navigate = useNavigate();
  // const location = useLocation();

  const [page, setPage] = useState(location.pathname);

  const handlePage = (url: string) => {
    // setPage(url);
    // navigate(url);
  }

  return (
    <nav className={ styled.navbar }>
      <div onClick={() => handlePage('/busca')} className={ `${styled.navbar__item} ${page == "/busca" ? styled.navbar__item_active : ''}` }>
        <SearchIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Busca</h1>
      </div>
      <div onClick={() => handlePage('/inicio')} className={ `${styled.navbar__item} ${page == "/início" ? styled.navbar__item_active : ''}` }>
        <HomeIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Início</h1>
      </div>
      <div onClick={() => handlePage('/salvos')} className={ `${styled.navbar__item} ${page == "/salvos" ? styled.navbar__item_active : ''}` }>
        <MarkIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Salvos</h1>
      </div>
      <div onClick={() => handlePage('/perfil')} className={ `${styled.navbar__item} ${page == "/perfil" ? styled.navbar__item_active : ''}` }>
        <ProfileIcon className={ styled.icon }/>
        <h1 className={ styled.text }>Perfil</h1>
      </div>
    </nav>
  );
};
export default NavBar;