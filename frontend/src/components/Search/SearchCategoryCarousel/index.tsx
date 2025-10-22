"use client";
import Image from 'next/image'

import { Swiper, SwiperSlide } from 'swiper/react'
import { Navigation, Pagination, Grid } from 'swiper/modules';
import { Category } from '@/interfaces/Category';

import './style.scss'
import 'swiper/css'
import 'swiper/css/grid'
import 'swiper/css/navigation'
import 'swiper/css/pagination'

import SearchCategoryCard from '@/components/Search/SearchCategoryCard'

interface CategoryCarouselProps {
  categories: Category[] | [];
  navigateFilter?: (id_category: Category) => void; 
}

export default function CategoryCarousel({ categories, navigateFilter }: CategoryCarouselProps) {
  
  const settings = {
    modules: [Navigation, Pagination, Grid],
    spaceBetween: 10,
    slidesPerView: 2,
    grid: {
        cols: "auto",
        rows: 2,
        fill: 'row' as 'row'
    },
    pagination: { clickable: true },
  };

  return (
    <Swiper {...settings} className="search_category_carousel">
      {categories.map((category) => (
        <SwiperSlide key={ category.id_category }>
            <SearchCategoryCard category={ category } isActive={ false } />
        </SwiperSlide>
      ))}
    </Swiper>
  );
};