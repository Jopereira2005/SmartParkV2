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

interface CategoryCarouselProps {
  categories: Category[] | [];
}

export default function CategoryCarousel({ categories }: CategoryCarouselProps) {
  const settings = {
    modules: [Navigation, Pagination, Grid],
    spaceBetween: 10,
    slidesPerView: 2,
    grid: {
        cols: 2,
        rows: 2,
        fill: 'row' as 'row'
    },
    pagination: { clickable: true },
  };

  return (
    <Swiper {...settings} className="home_category_carousel">
      { categories.map((category) => (
        <SwiperSlide key={category.id_category}>
            <Image
              className="category_card_image"
              src={ category.image || "/images/Estacionamento.png" }
              alt={ category.name }
              width={80}
              height={80}
            />
            <h2 className="category_card_title">{ category.name }</h2>
        </SwiperSlide>
      ))}
    </Swiper>
  );
};